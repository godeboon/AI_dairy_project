# connection.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.config.settings import settings

# settings에서 데이터베이스 URL 가져오기
SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# ✅ 여기가 빠져 있던 핵심!
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

print("✅ connection.py 불러오기 성공")
print("✅ Base 정의 완료:", Base)

import os
print("📢📢📢📢SERVER CWD:", os.getcwd())
print("📢📢📢📢SERVER DB ABS:", os.path.abspath(engine.url.database))
