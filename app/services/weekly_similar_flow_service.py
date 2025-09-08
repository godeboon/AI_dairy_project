from __future__ import annotations
from typing import Dict, List
import json
from datetime import datetime

from app.core.connection import get_db
from app.models.db.study_model import WeeklyAnalysisReport, SimilarPattern
from app.models.db.session_summary import GPTSessionSummary
from app.repositories.weekly_analysis_repository import WeeklyAnalysisRepository
from app.repositories.similar_pattern_repository import SimilarPatternRepository
from app.services.similar_pattern_service import SimilarPatternService
from app.prompt.similar_sessions_prompt import build_weekly_vs_past_comparison_prompt
from app.clients.gpt_api import call_gpt
from app.tasks.similar_pattern_event_check import check_similar_pattern_analysis_ready


class WeeklySimilarFlowService:
    def __init__(self):
        self.sim = SimilarPatternService()

    def run(self, user_id: int, analysis_id: int) -> Dict[str, object]:
        """
        주간 리포트 저장 이후 호출되는 오케스트레이션 흐름:
          1) used_dates 파싱 → yymmdd 변환 → GPTSessionSummary 조회
          2) 일주일치 분석 내용을 순서대로 연결
          3) 과거 유사 세션들과 비교 분석
          4) SimilarPattern 테이블에 저장/업데이트
        """
        db = next(get_db())
        try:
            # 1. WeeklyAnalysisReport 조회
            report = (
                db.query(WeeklyAnalysisReport)
                .filter(WeeklyAnalysisReport.analysis_id == analysis_id)
                .first()
            )
            if not report:
                return {"ok": False, "reason": "weekly_report_not_found"}

            # 2. used_dates 파싱 및 yymmdd 변환
            yymmdd_list = self._parse_used_dates_to_yymmdd(report.used_dates)
            print(f"🔍 [DEBUG] 변환된 yymmdd 리스트: {yymmdd_list}")
            
            # 3. 일주일치 세션 요약 조회 (yymmdd ASC, 00n ASC)
            weekly_summaries = self._get_weekly_session_summaries_ordered(
                db, user_id, yymmdd_list
            )
            print(f"🔍 [DEBUG] 일주일치 세션 수: {len(weekly_summaries)}")

            # 4. query 구성
            query = self._build_query_from_keyword_pattern(report.keyword_pattern_result)
            print(f"🔍 [DEBUG] 분석 query: {query}")

            # 5. 유사 세션 찾기
            print(f"🔍 [DEBUG] 유사 세션 검색 시작: user_id={user_id}, analysis_id={analysis_id}, query='{query}'")
            session_ids: List[str] = self.sim.get_similar_session_ids(
                user_id=user_id,
                analysis_id=analysis_id,
                query=query,
                top_k=150,
                min_similarity=0.55,
            )
            print(f"🔍 [DEBUG] 벡터에서 찾아진 유사 세션 수: {len(session_ids)}")
            print(f"🔍 [DEBUG] 벡터에서 찾아진 유사 세션들: {session_ids}")
            
            if not session_ids:
                print(f"🔍 [DEBUG] 유사한 세션이 없음")
                return {"ok": True, "prompt": "유사한 세션이 없습니다.", "sessions": []}

            # 6. 과거 유사 세션 내용 조회
            repo = WeeklyAnalysisRepository(db)
            grouped: Dict[str, List[Dict[str, object]]] = {}
            
            def _n_key(sid: str) -> int:
                try:
                    return int(sid.split("_")[1])
                except Exception:
                    return 10**9

            for sid in session_ids:
                yymmdd = (sid.split("_")[0] if "_" in sid else sid[:6]).strip()
                chats = repo.session_id_chats(user_id=user_id, session_id=sid)
                if not chats:
                    continue
                grouped.setdefault(yymmdd, []).append({"sid": sid, "chats": chats})

            for y in list(grouped.keys()):
                grouped[y].sort(key=lambda x: _n_key(x["sid"]))

            # 7. 프롬프트 생성 및 GPT 호출
            prompt_text = build_weekly_vs_past_comparison_prompt(
                weekly_summaries, grouped, query
            )
            print(f"🔍 [DEBUG] 프롬프트 생성 완료")
            print(f"similar 프롬프트 {prompt_text}")

            # 8. GPT 호출 및 응답 파싱
            gpt_response = self._call_gpt_and_parse(prompt_text)
            print(f"similar 응답내용 {gpt_response}")
            
            # 9. SimilarPattern 저장/업데이트
            print(f"🔍 [DEBUG] SimilarPattern 저장/업데이트 시작")
            print(f"🔍 [DEBUG] 저장할 데이터: user_id={user_id}, analysis_id={analysis_id}")
            print(f"🔍 [DEBUG] 저장할 query: '{query}'")
            print(f"🔍 [DEBUG] 저장할 session_ids: {session_ids}")
            print(f"🔍 [DEBUG] 저장할 gpt_response: {gpt_response}")
            
            similar_pattern_repo = SimilarPatternRepository(db)
            print(f"similar repo 호출 성공")
            similar_pattern_repo.save_or_update_pattern(
                user_id, analysis_id, query, session_ids, gpt_response
            )
            print(f"🔍 [DEBUG] SimilarPattern 저장/업데이트 완료")
            
            # 10. 유사 패턴 분석 준비 상태 체크 태스크 호출
            try:
                check_similar_pattern_analysis_ready.delay(user_id)
                print(f"✅ 유사 패턴 분석 준비 상태 체크 태스크 호출 완료: user_id={user_id}")
            except Exception as e:
                print(f"❌ 유사 패턴 분석 준비 상태 체크 태스크 호출 실패: {e}")

            return {
                "ok": True, 
                "prompt": prompt_text, 
                "weekly_sessions": weekly_summaries,
                "similar_sessions": session_ids,
                "query": query,
                "insights": gpt_response
            }
        finally:
            db.close()

    def _parse_used_dates_to_yymmdd(self, used_dates_json) -> List[str]:
        """used_dates JSON을 파싱하여 yymmdd 리스트 반환 (오름차순)"""
        if isinstance(used_dates_json, str):
            dates = json.loads(used_dates_json)
        else:
            dates = used_dates_json or []
        
        yymmdd_list = []
        for date_str in dates:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                yymmdd = dt.strftime("%y%m%d")
                yymmdd_list.append(yymmdd)
            except Exception as e:
                print(f"❌ 날짜 변환 실패: {date_str} - {e}")
        
        yymmdd_list.sort()  # 오름차순 정렬
        return yymmdd_list
    


    def _get_weekly_session_summaries_ordered(self, db, user_id: int, yymmdd_list: List[str]) -> List[Dict]:
        """일주일치 세션 요약들을 yymmdd ASC, 00n ASC 순서로 조회"""
        summaries = []
        for yymmdd in yymmdd_list:
            # 해당 날짜의 모든 세션 요약 조회 (session_id 오름차순 = 00n 오름차순)
            daily_summaries = db.query(GPTSessionSummary).filter(
                GPTSessionSummary.user_id == user_id,
                GPTSessionSummary.session_id.like(f"{yymmdd}_%")
            ).order_by(GPTSessionSummary.session_id).all()
            
            for summary in daily_summaries:
                summaries.append({
                    "session_id": summary.session_id,
                    "summary": summary.summary,
                    "yymmdd": yymmdd
                })
        
        return summaries

    def _build_query_from_keyword_pattern(self, keyword_pattern_result) -> str:
        """keyword_pattern_result에서 검색용 쿼리 구성"""
        query = ""
        try:
            kpr = keyword_pattern_result
            if isinstance(kpr, str):
                kpr = json.loads(kpr)
            themes = [str(x).strip() for x in (kpr or {}).get("main_themes", []) if str(x).strip()]
            query = " ".join(themes)
            print(f"🔍 [DEBUG] keyword query: {query}")
        except Exception:
            query = ""
        return query

    def _call_gpt_and_parse(self, prompt_text: str) -> Dict[str, str]:
        """GPT 호출 및 JSON 응답 파싱"""
        try:
            prompt_for_gpt = [
                {"role": "system", "content": "당신은 사용자의 패턴을 분석하는 전문가입니다. 정확한 JSON 형태로 응답해주세요."},
                {"role": "user", "content": prompt_text}
            ]
            
            response = call_gpt(prompt_for_gpt)
            print(f"🤖 [DEBUG] GPT 응답: {response}")
            
            # JSON 파싱
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            parsed = json.loads(cleaned_response)
            
            result = {
                "유사한 패턴": parsed.get("유사한 패턴", "없음"),
                "성향": parsed.get("성향", "없음"),
                "무의식적 통찰": parsed.get("무의식적 통찰", "없음")
            }
            
            return result
        except Exception as e:
            print(f"❌ GPT 호출 또는 파싱 실패: {e}")
            return {
                "유사한 패턴": "없음",
                "성향": "없음", 
                "무의식적 통찰": "없음"
            }


