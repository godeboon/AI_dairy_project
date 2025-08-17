from sqlalchemy.orm import Session
from app.models.db.study_model import DiaryAnalysisReport, WeeklyAnalysisReport
from datetime import datetime, timedelta


class WeeklyAnalysisRepository:
    def __init__(self, db: Session):
        self.db = db
    
    # def get_weekly_reports(self, user_id: int, days: int = 7):
    #     """최근 N일간의 일일 분석 리포트 조회"""
    #     end_date = datetime.now()  # 시스템 로컬 시간 사용 (KST)
    #     start_date = end_date - timedelta(days=days)
        
    #     reports = self.db.query(DiaryAnalysisReport).filter(
    #         DiaryAnalysisReport.user_id == user_id,
    #         DiaryAnalysisReport.timestamp >= start_date,
    #         DiaryAnalysisReport.timestamp <= end_date
    #     ).order_by(DiaryAnalysisReport.timestamp.asc()).all()
        
    #     return reports
    
    def get_unused_weekly_reports(self, user_id: int, days: int = 7):
        """사용되지 않은 일일 분석 리포트 조회 (날짜순 정렬)"""
        unused_reports = self.db.query(DiaryAnalysisReport).filter(
            DiaryAnalysisReport.user_id == user_id,
            DiaryAnalysisReport.is_used_in_weekly == False
        ).order_by(DiaryAnalysisReport.timestamp.asc()).limit(days).all()
        
        return unused_reports
    
    def mark_reports_as_used(self, report_ids: list):
        """사용된 리포트들을 마킹"""
        self.db.query(DiaryAnalysisReport).filter(
            DiaryAnalysisReport.report_id.in_(report_ids)
        ).update({"is_used_in_weekly": True})
        self.db.commit()
    
    # def exists_weekly_analysis(self, user_id: int, week_start_date: str) -> bool:
    #     """해당 주의 주간 분석이 있는지 확인"""
    #     return self.db.query(WeeklyAnalysisReport).filter(
    #         WeeklyAnalysisReport.user_id == user_id,
    #         WeeklyAnalysisReport.week_start_date == week_start_date
    #     ).first() is not None
    
    def save_weekly_analysis(self, user_id: int, week_start_date: datetime, 
                           week_end_date: datetime, emotion_result: dict, 
                           keyword_result: dict, comprehensive_result: dict):
                           
        """주간 분석 결과 저장"""
        analysis = WeeklyAnalysisReport(
            user_id=user_id,
            week_start_date=week_start_date,
            week_end_date=week_end_date,
            emotion_trend_result=emotion_result,
            keyword_pattern_result=keyword_result,
            comprehensive_pattern_result=comprehensive_result,
            timestamp=datetime.now()  # 시스템 로컬 시간 사용 (KST)
        )
        self.db.add(analysis)
        self.db.commit()
        return analysis 