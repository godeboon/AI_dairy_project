import json
from sqlalchemy.orm import Session
from app.repositories.similar_pattern_repository import SimilarPatternRepository
from app.clients.gpt_api import call_gpt
from app.prompt.report_prompt import similar_pattern_comprehensive_analysis_prompt
from datetime import datetime
from typing import Optional, Dict, Any


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.similar_pattern_repo = SimilarPatternRepository(db)
    
    def generate_comprehensive_report(self, user_id: int, similar_pattern_id: int) -> Optional[Dict[str, Any]]:
        """유사 패턴 종합 분석 리포트 생성"""
        print(f"🔍 유사 패턴 종합 분석 시작: user_id={user_id}")
        
        try:
            # 1. similar_pattern_id와 user_id로 SimilarPattern 조회 (더 안전한 조회)
            similar_pattern = self.similar_pattern_repo.get_by_id_and_user_id(similar_pattern_id, user_id)
            
            if not similar_pattern:
                print(f"❌ 유사 패턴 데이터를 찾을 수 없음: similar_pattern_id={similar_pattern_id}, user_id={user_id}")
                return None
            
            # 2. 데이터 검증 (3개 이상인지 확인)
            analysis_ids = similar_pattern.analysis_ids
            queries = similar_pattern.queries
            pattern_insights = similar_pattern.pattern_insights
            
            if len(analysis_ids) < 3 or len(queries) < 3 or len(pattern_insights) < 3:
                print(f"❌ 분석 데이터가 부족함: analysis_ids={len(analysis_ids)}, queries={len(queries)}, pattern_insights={len(pattern_insights)}")
                return None
            
            print(f"✅ 데이터 검증 완료: analysis_ids={len(analysis_ids)}, queries={len(queries)}, pattern_insights={len(pattern_insights)}")
            
            # 3. 프롬프트 구성
            prompt = [
                {"role": "system", "content": "당신은 심리학적 패턴 분석 전문가입니다. 사용자의 반복되는 패턴을 종합하여 심층적인 심리 분석을 제공해주세요."},
                {"role": "user", "content": similar_pattern_comprehensive_analysis_prompt.format(
                    queries=queries,
                    pattern_insights=pattern_insights
                )}
            ]
            print(f"report프롬프트 : {prompt}")
            
            # 4. GPT API 호출
            print(f"🤖 GPT API 호출 시작")
            response = call_gpt(prompt)
            print(f"🤖 GPT 응답 원본: {response}")
            
            # 5. 응답 정리 (마크다운 코드 블록 제거)
            cleaned_response = self._clean_gpt_response(response)
            print(f"🧹 정리된 응답: {cleaned_response[:100]}...")
            
            # 6. JSON 파싱
            try:
                result = json.loads(cleaned_response)
                print(f"✅ JSON 파싱 성공: {list(result.keys())}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 실패: {e}")
                print(f"🔍 파싱 실패한 응답: {cleaned_response}")
                raise Exception(f"GPT 응답이 유효한 JSON이 아닙니다: {e}")
            
            # 7. GPT 응답 분리 및 가공
            integrated_topic = result["통합된 주제"]  # query에 저장할 통합된 주제
            
            # 나머지 3개를 하나의 JSON으로 합치기
            report_insights = {
                "정서적 패턴": result["정서적 패턴"],
                "성향": result["성향"],
                "무의식적 통찰": result["무의식적 통찰"]
            }
            
            # 8. PersonalityReport 테이블에 저장
            from app.models.db.study_model import PersonalityReport
            
            personality_report = PersonalityReport(
                user_id=user_id,
                query=integrated_topic,  # 통합된 주제를 query에 저장
                report_result=report_insights,  # 나머지 3개 JSON을 report_result에 저장
                timestamp=datetime.now(),
                date_str=datetime.now().strftime("%Y-%m-%d")
            )
            
            self.db.add(personality_report)
            self.db.commit()
            
            print(f"✅ PersonalityReport DB 저장 완료: user_id={user_id}")
            
            # 9. 결과 반환 (DB 저장에 필요한 것만)
            report_result = {
                "user_id": int(user_id),
                "personality_report_id": personality_report.id,
                "integrated_topic": integrated_topic,
                "timestamp": datetime.now(),
                "date_str": datetime.now().strftime("%Y-%m-%d")
            }
            
            print(f"✅ 유사 패턴 종합 분석 완료: user_id={user_id}")
            return report_result
            
        except Exception as e:
            print(f"❌ 유사 패턴 종합 분석 실패: {str(e)}")
            raise Exception(f"종합 분석 중 오류 발생: {e}")
    
    def _clean_gpt_response(self, response: str) -> str:
        """GPT 응답에서 마크다운 코드 블록 제거"""
        cleaned_response = response.strip()
        
        # ```json 제거
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        
        # 끝의 ``` 제거
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        
        return cleaned_response.strip()
