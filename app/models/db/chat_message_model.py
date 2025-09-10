from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.core.connection import Base

# 채팅 메시지 모델
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)      # 메시지 고유 ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)                            # 유저 ID (users.id 참조)
    session_id = Column(String,ForeignKey("session_logs.session_id"), nullable=False)              # 세션 ID (확장 가능성 고려)
    role = Column(String, nullable=False)                   # 'user' or 'gpt'
    message = Column(String, nullable=False)                # 메시지 내용
    timestamp = Column(DateTime, default=func.now())        # 생성 시각
    turn = Column(Integer)                                  
    


print ("✅ chatmessage 모델 생성완료")                               
