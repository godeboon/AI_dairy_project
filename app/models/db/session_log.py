from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, func
from app.core.connection import Base


class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, nullable=False)

    # 세션 타임스탬프
    start_time = Column(DateTime, server_default=func.now(), nullable=False)  # 세션 시작 시각
    end_time = Column(DateTime, nullable=True)                                # 세션 종료 시각

    # 임베딩 진행 상태
    emb_started_at = Column(DateTime, nullable=True)
    emb_finished_at = Column(DateTime, nullable=True)
    emb_success = Column(Boolean, default=False, nullable=False)
    emb_error = Column(Text, nullable=True)

print(" ✅ sessionlog 클래스정의 ")
