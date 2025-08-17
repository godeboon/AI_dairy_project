from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.token_utils import decode_token
from app.models.schemas.auth_schema import UserInToken
from app.core.connection import get_db
from app.models.db.user_model import User
from jose import JWTError

# FastAPI가 토큰을 가져오는 방식 지정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# 의존성 함수 정의
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_token(token)
        user_data = UserInToken(**payload)
        user = db.query(User).get(user_data.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return user
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="인증 실패: 유효하지 않은 토큰입니다.")
