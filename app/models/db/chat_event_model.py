from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.core.connection import Base

class ChatEvent(Base):
    __tablename__ = "chat_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)  # "open" or "close"
    timestamp = Column(DateTime, default=func.now(), nullable=False)


print(" ✅ chatevent 모델 생성")