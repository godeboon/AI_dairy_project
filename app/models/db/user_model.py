# models/user_model.py

from sqlalchemy import Column, Integer, String
from app.core.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)                    # 내부용 자동 증가 고유 ID
    username = Column(String, unique=True, nullable=False)               # 사용자가 입력하는 고유 아이디
    email = Column(String, unique=True, index=True, nullable=False)      # 이메일 (중복 방지)
    hashed_password = Column(String, nullable=False)                     # 암호화된 비밀번호
    nickname = Column(String, nullable=False)                            # 유저 닉네임



print("✅ User 클래스 정의됨:", User)
