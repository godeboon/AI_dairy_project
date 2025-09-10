from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey, UniqueConstraint, func
from app.core.connection import Base

class DiaryReport(Base):
    __tablename__ = "diary_reports"
    
    diary_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 사용자 ID 추가
    content = Column(Text)
    source_type = Column(String(20))  # 'user' or 'ai'
    timestamp = Column(DateTime, default=func.now())
    
    # 하루에 한 번만 일기 작성 가능하도록 제약조건
    __table_args__ = (
        UniqueConstraint("user_id", "timestamp", name="uix_user_diary"),  # 정확히는 중복되지만 일단 유지
    )

class DiaryAnalysisReport(Base):
    __tablename__ = "diary_analysis_reports"
    
    report_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    emotions = Column(JSON, nullable=False)  # ["슬픔", "사랑", "기쁨"]
    scores = Column(JSON, nullable=False)    # [0.3, 0.5, 0.2]
    keywords = Column(JSON, nullable=False)  # ["친구", "대화", "고민"]
    keyword_descriptions = Column(JSON, nullable=False)  # ["친구와 세명이서 만나는날 나는 모르는 이야기가 오고가서 소외감을 느낌", "대화에서 고민을 나누었다", "고민을 해결하려고 노력했다"]
    summary = Column(Text, nullable=False)   # "친구와의 대화에서 고민을 나누었다"
    timestamp = Column(DateTime, default=func.now(), nullable=False)  # 정확한 시간 정보
    date_str = Column(String(10), nullable=False)  # "2024-01-15" - 간단한 날짜 표현
    is_used_in_weekly = Column(Boolean, default=False)  # 주간 분석에 사용되었는지 여부


class WeeklyAnalysisReport(Base):
    __tablename__ = "weekly_analysis_reports"
    
    analysis_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 외래키 추가
    week_start_date = Column(DateTime)
    week_end_date = Column(DateTime)
    used_dates = Column(JSON)  # ["2024-01-13", "2024-01-15", ...] - 실제 사용된 날짜들
    
    # 체인 분석 결과들
    emotion_trend_result = Column(JSON)
    keyword_pattern_result = Column(JSON)
    comprehensive_pattern_result = Column(JSON)
    
    timestamp = Column(DateTime, default=func.now())


class EncouragementReport(Base):
    __tablename__ = "encouragement_reports"
    
    encouragement_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    encourage_content = Column(Text)
    music = Column(JSON, nullable=False)  # ["summer 노래", "겨울 노래"]
    singer = Column(JSON, nullable=False)  # ["아이유", "방탄소년단"]
    timestamp = Column(DateTime, default=func.now()) 

class SimilarPattern(Base):
    __tablename__ = "similar_patterns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    analysis_ids = Column(JSON, nullable=False)  # [5, 20, 35, ...]
    queries = Column(JSON, nullable=False)  # ["query1", "query2", ...]
    similar_session_ids = Column(JSON, nullable=False)  # [[250808_003, 250817_005], [251017_004], ...]
    pattern_insights = Column(JSON, nullable=False)  # JSON 형태로 3개 항목 저장
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_used_in_personality_analysis = Column(Boolean, default=False)  # 성격 분석에 사용되었는지 여부
    
    # __table_args__ = (
    #     UniqueConstraint("user_id", "analysis_ids", name="uix_user_analysis_ids"),
    # ) 


class PersonalityReport(Base):
    __tablename__ = "personality_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(JSON, nullable=False)  # JSON 형태로 저장
    report_result = Column(JSON, nullable=False)  # JSON 형태로 저장
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    date_str = Column(String(10), nullable=False)  # strftime으로 가공된 날짜 문자열 