from sqlalchemy.orm import Session
from app.models.db.study_model import DiaryAnalysisReport, WeeklyAnalysisReport
from app.models.db.chat_message_model import ChatMessage
from app.models.db.user_model import User
from datetime import datetime, timedelta
from sqlalchemy import func


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
    
    def get_users_with_unused_reports(self, days: int = 7):
        """7일치 미사용 리포트가 있는 사용자들 조회"""
        # 서브쿼리로 7일치 미사용 리포트가 있는 사용자 ID 조회
        subquery = self.db.query(DiaryAnalysisReport.user_id).filter(
            DiaryAnalysisReport.is_used_in_weekly == False
        ).group_by(DiaryAnalysisReport.user_id).having(
            func.count(DiaryAnalysisReport.report_id) >= days
        ).subquery()
        
        return self.db.query(User).filter(User.id.in_(subquery)).all()
    
    def check_weekly_analysis_exists(self, user_id: int, week_start_date: datetime) -> bool:
        """해당 주의 주간 분석이 이미 존재하는지 확인 (start_date 기준)"""
        return self.db.query(WeeklyAnalysisReport).filter(
            WeeklyAnalysisReport.user_id == user_id,
            WeeklyAnalysisReport.week_start_date == week_start_date
        ).first() is not None
    
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
                           week_end_date: datetime, used_dates: list,
                           emotion_result: dict, keyword_result: dict, 
                           comprehensive_result: dict):
                           
        """주간 분석 결과 저장"""
        print(f"🔍 [DEBUG] save_weekly_analysis - used_dates: {used_dates}, type: {type(used_dates)}")
        analysis = WeeklyAnalysisReport(
            user_id=user_id,
            week_start_date=week_start_date,
            week_end_date=week_end_date,
            used_dates=used_dates,
            emotion_trend_result=emotion_result,
            keyword_pattern_result=keyword_result,
            comprehensive_pattern_result=comprehensive_result,
            timestamp=datetime.now()  # 시스템 로컬 시간 사용 (KST)
        )
        self.db.add(analysis)
        self.db.commit()
        return analysis 

    def session_id_chats(self, user_id: int, session_id: str) -> list[str]:
        """
        특정 user_id + session_id의 user 메시지만 수집하여 formatted_chats 스타일로 반환.
        포맷: 'user: {message}'
        정렬: turn ASC, 보조로 timestamp ASC
        """
        rows = (
            self.db.query(ChatMessage)
            .filter(
                ChatMessage.user_id == user_id,
                ChatMessage.session_id == session_id,
                ChatMessage.role == "user",
            )
            .order_by(ChatMessage.turn.asc(), ChatMessage.timestamp.asc())
            .all()
        )

        formatted_chats: list[str] = []
        for chat in rows:
            formatted_chats.append(f"{chat.role}: {chat.message}")

        return formatted_chats