from sqlalchemy.orm import Session
from datetime import datetime, date
from app.prompt.diary_prompt import DiaryPromptService

from app.models.db.study_model import DiaryReport
from app.repositories.today_chat_message_repository import TodayChatMessageRepository
from app.models.schemas.study_schema import DiaryResponse
from app.clients.gpt_api import GPTClient
from app.core.connection import get_db
from app.config.settings import settings
import json
import redis

class DiaryService:
    def __init__(self):
        self.prompt_service = DiaryPromptService()
        self.chat_repository = TodayChatMessageRepository()
        self.gpt_client = GPTClient()
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db
        )

    async def check_diary_conditions(self, user_id: int):
        """일기 생성 조건 체크 - 라우터와 동일한 로직"""
        try:
            # 오늘 AI 생성 여부 확인 (source_type='ai')
            today_ai_diary = self.chat_repository.check_today_diary_by_source(user_id, 'ai')
            if today_ai_diary:
                return {
                    "available": False
                }
            
            # 오늘 사용자 채팅 토큰수 확인
            formatted_chats, total_tokens = self.chat_repository.diary_get_today_user_chat_and_tokens(user_id)
            min_tokens = 55  # 최소 토큰수 설정
            if total_tokens < min_tokens:
                return {
                    "available": False
                }
            
            return {
                "available": True
            }
            
        except Exception as e:
            return {
                "available": False
            }
        



    async def generate_diary_stream(self, user_id: int):
        """스트리밍 방식으로 일기 생성"""
        db = next(get_db())
        try:
            # 1. 오늘 사용자 채팅 데이터 가져오기
            formatted_chats, total_tokens = self.chat_repository.diary_get_today_user_chat_and_tokens(user_id)
            
            # 2. 프롬프트 생성
            prompt = self.prompt_service.generate_diary_prompt(formatted_chats)
            
            # 3. 스트리밍 GPT 호출 및 실시간 전송
            full_content = ""
            async for chunk in self.gpt_client.stream_gpt_response(prompt):
                full_content += chunk
                yield chunk  # 실시간으로 프론트에 전송
            
            # 4. 스트리밍 완료 후 DB 저장
            diary_report = DiaryReport(
                user_id=user_id,
                content=full_content, 
                source_type='ai',
                timestamp=datetime.now()  # 시스템 로컬 시간 사용 (KST)
            )
            db.add(diary_report)
            db.commit()
            
            print(f"✅ AI 일기 생성 완료 및 DB 저장: user_id={user_id}")
            
            # 5. Redis를 통한 실시간 알림 발행 (WebSocketService가 구독하여 WebSocket으로 전송)
            message = {
                "type": "diary_unavailable",
                "channel": "realtime",
                "priority": "high",
                "reason": "ai_diary_created"
            }
            
            channel = f"user_{user_id}_diary"
            message_json = json.dumps(message)
            
            print(f"📤 diary_unavailable Redis 발행 시도: channel={channel}, message={message_json}")
            
            try:
                result = self.redis_client.publish(channel, message_json)
                print(f"✅ diary_unavailable Redis 발행 성공: channel={channel}, result={result} (구독자 수)")
                
                # 발행 성공 후 잠시 대기 (중복 발송 방지)
                import time
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ diary_unavailable Redis 발행 실패: {e}")
            
        except Exception as e:
            print(f"❌ AI 일기 생성 중 오류: {e}")
            db.rollback()
            raise e
        finally:
            db.close()


    async def save_diary(self, user_id: int, content: str, source_type: str = 'ai'):
        """일기 저장"""
        db = next(get_db())
        try:
            diary_report = DiaryReport(
                user_id=user_id,
                content=content,
                source_type=source_type,
                timestamp=datetime.now()  # 시스템 로컬 시간 사용 (KST)
            )
            db.add(diary_report)
            db.commit()
            return diary_report
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
