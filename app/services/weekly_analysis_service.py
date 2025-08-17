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
            
            analysis = self.weekly_repo.save_weekly_analysis(
                user_id=user_id,
                week_start_date=week_start,
                week_end_date=week_end,
                emotion_result=emotion_result,
                keyword_result=keyword_result,
                comprehensive_result=comprehensive_result
            )
            
            # 5. 사용된 리포트들 마킹
            report_ids = [report.report_id for report in unused_reports]
            self.weekly_repo.mark_reports_as_used(report_ids)
            
            print(f"✅ 주간 분석 완료: user_id={user_id}")
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
            {"role": "system", "content": "당신은 감정 분석 전문가입니다. 정확한 JSON 형태로 응답해주세요."},
            {"role": "user", "content": emotion_trend_prompt.format(
                weekly_emotions=weekly_data["weekly_emotions"],
                weekly_scores=weekly_data["weekly_scores"]
            )}
        ]
        
        response = call_gpt(prompt)
        return json.loads(response)
    
    def _analyze_keyword_pattern(self, weekly_data):
        """키워드 패턴 분석"""
        prompt = [
            {"role": "system", "content": "당신은 키워드 분석 전문가입니다. 정확한 JSON 형태로 응답해주세요."},
            {"role": "user", "content": keyword_pattern_prompt.format(
                weekly_keywords=weekly_data["weekly_keywords"]
            )}
        ]
        
        response = call_gpt(prompt)
        return json.loads(response)
    
    def _analyze_comprehensive(self, emotion_result, keyword_result, weekly_data):
        """종합 분석"""
        prompt = [
            {"role": "system", "content": "당신은 심리 분석 전문가입니다. 정확한 JSON 형태로 응답해주세요."},
            {"role": "user", "content": comprehensive_analysis_prompt.format(
                emotion_analysis=emotion_result,
                keyword_analysis=keyword_result,
                weekly_summaries=weekly_data["weekly_summaries"]
            )}
        ]
        
        response = call_gpt(prompt)
        return json.loads(response) 