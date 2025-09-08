import json
from sqlalchemy.orm import Session
from app.repositories.weekly_analysis_repository import WeeklyAnalysisRepository
from app.clients.gpt_api import call_gpt
from app.prompt.weekly_analysis_prompts import (
    emotion_trend_prompt, 
    keyword_pattern_prompt, 
    comprehensive_analysis_prompt
)
from datetime import datetime
from app.services.weekly_similar_flow_service import WeeklySimilarFlowService

class WeeklyAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.weekly_repo = WeeklyAnalysisRepository(db)
    
    def analyze_weekly_data(self, user_id: int):
        """7일간 데이터로 주간 분석 실행"""
        
        # 1. 사용되지 않은 7일간 일일 분석 리포트 조회
        unused_reports = self.weekly_repo.get_unused_weekly_reports(user_id, 7)
        
        if len(unused_reports) < 7:
            print(f"❌ 7일간 데이터 부족: {len(unused_reports)}일")
            return None
        
        # 2. 데이터 준비
        weekly_data = self._prepare_weekly_data(unused_reports)
        
        # 3. 순차적 체인 분석 실행
        try:
            # 3-1. 감정 변화 분석
            emotion_result = self._analyze_emotion_trend(weekly_data)
            
            # 3-2. 키워드 패턴 분석
            keyword_result = self._analyze_keyword_pattern(weekly_data)
            
            # 3-3. 종합 분석
            comprehensive_result = self._analyze_comprehensive(
                emotion_result, keyword_result, weekly_data
            )
            
            # 4. 결과 저장
            week_start = unused_reports[0].timestamp
            week_end = unused_reports[-1].timestamp
            
            # used_dates 준비 (날짜 문자열 리스트) - JSON 컬럼에 맞게 처리
            used_dates = [report.date_str for report in unused_reports]
            print(f"🔍 [DEBUG] used_dates 생성: {used_dates}")
            
            # JSON 컬럼 호환성을 위해 명시적 변환 시도
            try:
                import json
                used_dates_json = json.dumps(used_dates, ensure_ascii=False)
                print(f"🔍 [DEBUG] used_dates JSON 변환: {used_dates_json}")
                used_dates = used_dates_json
            except Exception as e:
                print(f"⚠️ [WARN] JSON 변환 실패, 원본 리스트 사용: {e}")
            
            analysis = self.weekly_repo.save_weekly_analysis(
                user_id=user_id,
                week_start_date=week_start,
                week_end_date=week_end,
                used_dates=used_dates,
                emotion_result=emotion_result,
                keyword_result=keyword_result,
                comprehensive_result=comprehensive_result
            )
            
            # 5. 사용된 리포트들 마킹
            report_ids = [report.report_id for report in unused_reports]
            self.weekly_repo.mark_reports_as_used(report_ids)
            

            
            print(f"✅ 주간 분석 완료: user_id={user_id}")

            
            # 6. 주간 저장 이후 유사 세션 프롬프트 흐름 실행 (개발/운영 공통)
            try:
                flow = WeeklySimilarFlowService()
                flow_result = flow.run(user_id=user_id, analysis_id=analysis.analysis_id)
                print("flow 서비스호출 ")
                if flow_result and flow_result.get("ok"):
                    print("🔁 [DEBUG] 유사 세션 프롬프트 생성 완료")
                else:
                    print("⚠️ [WARN] 유사 세션 프롬프트 생성 실패 또는 없음:", flow_result)
            except Exception as _e:
                print(f"⚠️ [WARN] 유사 세션 흐름 실행 중 예외: {_e}")
            return analysis
            
        except Exception as e:
            print(f"❌ 주간 분석 실패: {str(e)}")
            return None
    
    def _prepare_weekly_data(self, weekly_reports):
        """주간 데이터 준비"""
        weekly_emotions = [report.emotions for report in weekly_reports]
        weekly_scores = [report.scores for report in weekly_reports]
        weekly_keywords = [report.keywords for report in weekly_reports]
        weekly_summaries = [report.summary for report in weekly_reports]
        
        return {
            "weekly_emotions": weekly_emotions,
            "weekly_scores": weekly_scores,
            "weekly_keywords": weekly_keywords,
            "weekly_summaries": weekly_summaries
        }
    
    def _analyze_emotion_trend(self, weekly_data):
        """감정 변화 분석"""
        prompt = [
            {"role": "system", "content": "당신은 사용자 한명의 개인의 감정을 분석 전문가입니다. 정확한 JSON 형태로 응답해주세요."},
            {"role": "user", "content": emotion_trend_prompt.format(
                weekly_emotions=weekly_data["weekly_emotions"],
                weekly_scores=weekly_data["weekly_scores"]
            )}
        ]
        
        print(f"🔍 [DEBUG] 감정 변화 분석 프롬프트 전송")
        response = call_gpt(prompt)
        print(f"🤖 [DEBUG] 감정 변화 분석 GPT 응답 원본: {response}")
        
        # 마크다운 코드 블록 제거 (```json, ```)
        cleaned_response = response.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]  # ```json 제거
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]   # ``` 제거
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]  # 끝의 ``` 제거
        
        cleaned_response = cleaned_response.strip()
        print(f"🧹 [DEBUG] 감정 변화 분석 정리된 응답 길이: {len(cleaned_response)}")
        print(f"🧹 [DEBUG] 감정 변화 분석 정리된 응답 첫 100자: {cleaned_response[:100]}")
        
        # JSON 파싱 예외 처리
        try:
            result = json.loads(cleaned_response)
            print(f"✅ [DEBUG] 감정 변화 분석 JSON 파싱 성공: {list(result.keys())}")
            return result
        except json.JSONDecodeError as e:
            print(f"❌ [ERROR] 감정 변화 분석 JSON 파싱 실패: {e}")
            print(f"🔍 [DEBUG] 파싱 실패한 응답: {cleaned_response}")
            raise Exception(f"감정 변화 분석 GPT 응답이 유효한 JSON이 아닙니다: {e}")
    
    def _analyze_keyword_pattern(self, weekly_data):
        """키워드 패턴 분석"""
        prompt = [
            {"role": "system", "content": "당신은 사용자(한명,개인)의 키워드 분석 전문가입니다. 정확한 JSON 형태로 응답해주세요."},
            {"role": "user", "content": keyword_pattern_prompt.format(
                weekly_keywords=weekly_data["weekly_keywords"]
            )}
        ]
        
        print(f"🔍 [DEBUG] 키워드 패턴 분석 프롬프트 전송")
        response = call_gpt(prompt)
        print(f"🤖 [DEBUG] 키워드 패턴 분석 GPT 응답 원본: {response}")
        
        # 마크다운 코드 블록 제거 (```json, ```)
        cleaned_response = response.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]  # ```json 제거
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]   # ``` 제거
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]  # 끝의 ``` 제거
        
        cleaned_response = cleaned_response.strip()
        print(f"🧹 [DEBUG] 키워드 패턴 분석 정리된 응답 길이: {len(cleaned_response)}")
        print(f"🧹 [DEBUG] 키워드 패턴 분석 정리된 응답 첫 100자: {cleaned_response[:100]}")
        
        # JSON 파싱 예외 처리
        try:
            result = json.loads(cleaned_response)
            print(f"✅ [DEBUG] 키워드 패턴 분석 JSON 파싱 성공: {list(result.keys())}")
            return result
        except json.JSONDecodeError as e:
            print(f"❌ [ERROR] 키워드 패턴 분석 JSON 파싱 실패: {e}")
            print(f"🔍 [DEBUG] 파싱 실패한 응답: {cleaned_response}")
            raise Exception(f"키워드 패턴 분석 GPT 응답이 유효한 JSON이 아닙니다: {e}")
    
    def _analyze_comprehensive(self, emotion_result, keyword_result, weekly_data):
        """종합 분석"""
        prompt = [
            {"role": "system", "content": "당신은 사용자(한명,개인)의 심리를 분석 전문가입니다. 정확한 JSON 형태로 응답해주세요."},
            {"role": "user", "content": comprehensive_analysis_prompt.format(
                emotion_analysis=emotion_result,
                keyword_analysis=keyword_result,
                weekly_summaries=weekly_data["weekly_summaries"]
            )}
        ]
        
        print(f"🔍 [DEBUG] 종합 분석 프롬프트 전송")
        response = call_gpt(prompt)
        print(f"🤖 [DEBUG] 종합 분석 GPT 응답 원본: {response}")
        
        # 마크다운 코드 블록 제거 (```json, ```)
        cleaned_response = response.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]  # ```json 제거
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]   # ``` 제거
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]  # 끝의 ``` 제거
        
        cleaned_response = cleaned_response.strip()
        print(f"🧹 [DEBUG] 종합 분석 정리된 응답 길이: {len(cleaned_response)}")
        print(f"🧹 [DEBUG] 종합 분석 정리된 응답 첫 100자: {cleaned_response[:100]}")
        
        # JSON 파싱 예외 처리
        try:
            result = json.loads(cleaned_response)
            print(f"✅ [DEBUG] 종합 분석 JSON 파싱 성공: {list(result.keys())}")
            return result
        except json.JSONDecodeError as e:
            print(f"❌ [ERROR] 종합 분석 JSON 파싱 실패: {e}")
            print(f"🔍 [DEBUG] 파싱 실패한 응답: {cleaned_response}")
            raise Exception(f"종합 분석 GPT 응답이 유효한 JSON이 아닙니다: {e}") 