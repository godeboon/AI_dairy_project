from pydantic_settings import BaseSettings
from typing import Optional
import os
from pydantic import Field

class Settings(BaseSettings):
    # 환경 구분
    environment: str = "development"
    
    # 데이터베이스 설정
    database_url: str = "sqlite:///./test.db"
    
    # API 키 설정
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    mixtral_token: str = Field(default="", env="MIXTRAL_TOKEN")
    mixtral_endpoint: str = Field(default="", env="MIXTRAL_ENDPOINT")
    
    # 보안 설정
    secret_key: str = Field(default="your-secret-key", env="SECRET_KEY")
    access_token_expire_minutes: int = 30
    
    # Redis 설정
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # 애플리케이션 설정
    app_name: str = "Matabus Chat API"
    debug: bool = True
    log_level: str = "INFO"
    
    # 성능 설정 , 실제 사용되고 있있지 않음 
    rate_limit_per_minute: int = 60
    max_concurrent_requests: int = 10
    
    # Chroma 연결 설정
    chroma_host: Optional[str] = None  # 예: "127.0.0.1" (None이면 파일모드 사용)
    chroma_port: int = 8000
    chroma_path: str = "C:/chroma_db"  # 서버 실행시 --path 와 일치 권장
    chroma_allow_reset: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False




settings = Settings() 