# models/login_log.py

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.connection import Base


class LoginLog(Base):
    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # 어떤 유저인지
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 로그인 시각 (자동 기록)
    login_time = Column(DateTime, default=datetime.now)
    
    # 로그아웃 시각 (처음엔 null, 로그아웃 시 업데이트)
    logout_time = Column(DateTime, nullable=True)

    # 유저와의 관계 (선택적: 필요 시 backref로 연결 가능)
    # user = relationship("User", back_populates="login_logs")

print ("loginlog 클래스 정의(모델)")