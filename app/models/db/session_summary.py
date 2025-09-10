from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, ForeignKeyConstraint, UniqueConstraint, func
from sqlalchemy.dialects.sqlite import JSON
from app.core.connection import Base

class SessionSummary(Base):
    __tablename__ = "session_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # ✅ 직접 FK 추가
    session_id = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "session_id", name="uix_user_session"),
        ForeignKeyConstraint(
            ["user_id", "session_id"],
            ["session_logs.user_id", "session_logs.session_id"]
        ),
    )


class GPTSessionSummary(Base):
    __tablename__ = "gpt_session_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, nullable=False)
    summary = Column(Text, nullable=False)  # 400자 요약본
    key_sentence = Column(Text, nullable=False)  # 핵심 문장
    keywords = Column(JSON, nullable=False)  # JSON 형태: ["갈등", "회사 동료", "스트레스", "고민", "대화"]
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "session_id", name="uix_gpt_user_session"),
        ForeignKeyConstraint(
            ["user_id", "session_id"],
            ["session_logs.user_id", "session_logs.session_id"]
        ),
    )


print(" ✅ gptsessionsummary 모델 생성완료(클래스정의) ")