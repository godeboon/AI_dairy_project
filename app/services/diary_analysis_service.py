import json
from sqlalchemy.orm import Session
from app.repositories.today_chat_message_repository import TodayChatMessageRepository
from app.models.db.study_model import DiaryAnalysisReport
from app.clients.gpt_api import call_gpt
from app.prompt.diary_analysis_report_prompt import diary_analysis_prompt
from datetime import datetime
from app.tasks.diary_analysis_event import check_weekly_analysis_after_diary_save


class DiaryAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.today_chat_repo = TodayChatMessageRepository()
    
    def analyze_user_diary(self, user_id: int):
        """사용자 다이어리 분석 (조건 체크 없이, 이미 조건 체크 celrey_app.py에서 끝냄 )"""
        
        # 1. user 채팅 내용 가져오기
        combined_content, total_tokens = self.today_chat_repo.get_today_user_chat_content_and_tokens(user_id)
        print(f"🔍 [DEBUG] user_id={user_id}, combined_content 길이: {len(combined_content)}")
        
        # 2. GPT API 호출 (시스템 메시지 + 사용자 메시지)
        prompt = [
            {"role": "system", "content": "당신은 하루의 일과를 다이어리로 기록해주는 역할입니다. 지나친 극존칭은 피해주세요. 정확한 JSON 형태로 응답해주세요."},
            {"role": "user", "content": diary_analysis_prompt.format(content=combined_content)}
        ]
        print ( f"🔍 promt : {prompt}" )
        
        # 3. GPT 호출                            
        response = call_gpt(prompt)
        print(f"🤖 [DEBUG] GPT 응답 원본: {response}")
        
        # 마크다운 코드 블록 제거 (```json, ```)
        cleaned_response = response.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]  # ```json 제거
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]   # ``` 제거
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]  # 끝의 ``` 제거
        
        cleaned_response = cleaned_response.strip()
        print(f"🧹 [DEBUG] 정리된 응답 길이: {len(cleaned_response)}")
        print(f"🧹 [DEBUG] 정리된 응답 첫 100자: {cleaned_response[:100]}")
        print(f"🧹 [DEBUG] 정리된 응답 마지막 50자: {cleaned_response[-50:]}")
        
        # JSON 파싱 예외 처리
        try:
            result = json.loads(cleaned_response)
            print(f"✅ [DEBUG] JSON 파싱 성공: {list(result.keys())}")
        except json.JSONDecodeError as e:
            print(f"❌ [ERROR] JSON 파싱 실패: {e}")
            print(f"🔍 [DEBUG] 파싱 실패한 응답: {cleaned_response}")
            raise Exception(f"GPT 응답이 유효한 JSON이 아닙니다: {e}")
        
        # 4. DB 저장
        try:
            analysis = DiaryAnalysisReport(
                user_id=user_id,
                emotions=result["emotions"],
                scores=result["scores"],
                keywords=result["keywords"],
                keyword_descriptions=result["keyword_descriptions"],
                summary=result["summary"],
                timestamp=datetime.now(),  # 시스템 로컬 시간 사용 (KST)
                date_str=datetime.now().strftime("%Y-%m-%d")  # 시스템 로컬 시간 기준 날짜 문자열
            )
            self.db.add(analysis)
            self.db.commit()
            print(f"💾 [DEBUG] DB 저장 성공: user_id={user_id}")
        except Exception as e:
            print(f"❌ [ERROR] DB 저장 실패: {e}")
            raise Exception(f"DB 저장 중 오류 발생: {e}")
        
        # 5. 이벤트 리스너 트리거 (주간 분석 체크)
        try:
            print(f"🚀 [DEBUG] 이벤트 리스너 트리거 시작: user_id={user_id}")
            check_weekly_analysis_after_diary_save.delay(user_id)
            print(f"✅ [DEBUG] 이벤트 리스너 트리거 성공: user_id={user_id}")
        except Exception as e:
            print(f"❌ [ERROR] 이벤트 리스너 트리거 실패: {e}")
            # 이벤트 트리거 실패는 치명적이지 않으므로 예외를 다시 발생시키지 않음
        
        return analysis 