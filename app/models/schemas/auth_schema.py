import re
from pydantic import BaseModel, EmailStr
from pydantic.functional_validators import field_validator  


# 1. ✅ 회원가입용 ( usercreate , register )
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    nickname: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("비밀번호에는 영문자가 포함되어야 합니다.")
        if not re.search(r"\d", v):
            raise ValueError("비밀번호에는 숫자가 포함되어야 합니다.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("비밀번호에는 특수문자가 포함되어야 합니다.")
        if re.search(r"(\d)\1{2,}", v):
            raise ValueError("비밀번호에 같은 숫자가 3번 이상 반복될 수 없습니다.")
        return v


# 2. ✅ 로그인용  ( /login )
class LoginInput(BaseModel):
    username: str
    password: str
    
# 3. ✅ 로그인 후 프론트에 응답할 JWT 토큰 포맷
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# 4. ✅ JWT 토큰 내부에 저장할 사용자 정보 구조 (ex: {"user_id": 1})
class UserInToken(BaseModel):
    user_id: int

print( "✅스키마 불러오기 성공" )


#5. 로그아웃용 

from pydantic import BaseModel

class LogoutInput(BaseModel):
    user_id: int
