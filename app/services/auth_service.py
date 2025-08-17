from fastapi import HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models.db.user_model import User
from app.core.token_utils import encode_token  # JWT 생성 함수
from datetime import datetime
from app.models.db.login_log import LoginLog  
from app.models.schemas.auth_schema import UserCreate


# ✅ 비밀번호 해시 비교 및 생성용 bcrypt 설정 (중복 제거)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ 로그인 검증 + 토큰 생성 함수
def authenticate_user(db: Session, username: str, password: str):
    """
    - DB에서 유저 정보 조회
    - 비밀번호 검증
    - 로그인 기록 저장
    - JWT 토큰 생성 및 반환
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")
    db.add(LoginLog(user_id=user.id, login_time=datetime.now()))
    db.commit()
    token = encode_token(user.id)
    return token

# ✅ 평문 비밀번호를 해시로 바꿔주는 함수
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# ✅ 유저 DB 저장 함수
def create_user(db: Session, user: UserCreate):
    """
    - 평문 비밀번호를 해시로 변환
    - User 모델 인스턴스 생성 및 DB 저장
    """
    hashed_pw = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw,
        nickname=user.nickname
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user 