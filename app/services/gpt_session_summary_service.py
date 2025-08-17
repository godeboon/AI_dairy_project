import json
import logging
from app.clients.gpt_api import call_gpt
from app.prompt.session_summary_prompt import build_session_summary_prompt
from app.repositories.today_chat_message_repository import TodayChatMessageRepository
from app.models.db.session_summary import GPTSessionSummary
from app.core.connection import get_db
from app.services.embedding_service import EmbeddingService
from app.models.db.session_log import SessionLog



logger = logging.getLogger(__name__)

class GPTSessionSummaryService:
    def __init__(self):
        self.chat_repo = TodayChatMessageRepository()
    
    def create_session_summary(self, user_id: int, session_id: str):
        """GPT를 사용하여 세션 요약 생성 및 DB 저장"""
        try:
            logger.info(f"▶ GPT 세션 요약 시작: user_id={user_id}, session_id={session_id}")
            
            # 1. 세션의 user 채팅 가져오기
            user_chats = self.chat_repo.today_session_user_chats_formatted(user_id, session_id)
            
            if not user_chats:
                logger.warning(f"⚠️ 세션에 user 채팅이 없음: user_id={user_id}, session_id={session_id}")
                return None
            
            # 2. 프롬프트 구성
            prompt = build_session_summary_prompt(user_chats)
            
            # 3. GPT 호출
            logger.info(f"🤖 GPT API 호출 중: user_id={user_id}, session_id={session_id}")
            response = call_gpt(prompt)
            print(f"📢 gpt_session_summary . response: {response}")
            
            # 4. JSON 파싱
            try:
                result = json.loads(response)
                summary = result.get("summary", "")
                key_sentence = result.get("key_sentence", "")
                keywords = result.get("keywords", [])
                
                # 키워드를 JSON 문자열로 변환
                keywords_json = json.dumps(keywords, ensure_ascii=False)
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 파싱 실패: {e}, response: {response}")
                return None
            
            # 5. DB 저장
            db = next(get_db())
            try:
                # 기존 요약본이 있는지 확인
                existing_summary = db.query(GPTSessionSummary).filter(
                    GPTSessionSummary.user_id == user_id,
                    GPTSessionSummary.session_id == session_id
                ).first()
                
                if existing_summary:
                    logger.info(f"ℹ️ 기존 요약본 업데이트: user_id={user_id}, session_id={session_id}")
                    existing_summary.summary = summary
                    existing_summary.key_sentence = key_sentence
                    existing_summary.keywords = keywords_json
                else:
                    logger.info(f"➕ 새 요약본 생성: user_id={user_id}, session_id={session_id}")
                    new_summary = GPTSessionSummary(
                        user_id=user_id,
                        session_id=session_id,
                        summary=summary,
                        key_sentence=key_sentence,
                        keywords=keywords_json
                    )
                    db.add(new_summary)
                
                db.commit()
                logger.info(f"✅ DB 저장 완료: user_id={user_id}, session_id={session_id}")

                # --- 임베딩 수행하기 + dense + sparse  ---
                try:
                    logger.info(f"▶ 임베딩 트리거: user_id={user_id}, session_id={session_id}")
                    res = EmbeddingService().create_session_embeddings(user_id, session_id)
                    logger.info(f"✅ 임베딩 결과: {res}")
                except Exception as e:
                    logger.exception(f"❌ 임베딩 트리거 실패: user_id={user_id}, session_id={session_id}, error={e}")
                # -----------------


                
                return {
                    "summary": summary,
                    "key_sentence": key_sentence,
                    "keywords": keywords
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"❌ DB 저장 실패: {e}")
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ GPT 세션 요약 실패: user_id={user_id}, session_id={session_id}, error={e}")
            raise

