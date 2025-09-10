from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.models.schemas.auth_schema import UserInToken
from app.config.settings import settings


# ✅ 비밀키, 알고리즘 설정 (Pydantic Settings가 이미 .env를 읽어줌)
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# ✅ 토큰 생성 함수 (user_id를 payload로 JWT 생성)
def encode_token(user_id: int):
    print(f"🛠️ encode_token: user_id = {user_id}")
    payload = UserInToken(user_id=user_id).dict()
    print(f"📦 payload before exp = {payload}")
    
    payload["exp"] = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    print(f"🕓 payload with exp = {payload}")

    try:
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        print(f"✅ 토큰 생성 완료: {token}")
        return token
    except Exception as e:
        print("❌ 토큰 생성 실패:", e)
        raise


# ✅ 토큰 검증 + 디코딩 함수 (JWT 문자열 → payload 추출)
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise ValueError("유효하지 않은 토큰입니다.")

print(f"✅ SECRET_KEY: {SECRET_KEY}")