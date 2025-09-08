from fastapi import FastAPI
from app.api.routers.html_router import router as html_router
from app.api.routers.auth_router import router as register_router
from app.core.connection import Base, engine
from app.api.routers.chat_message_router import router as chat_router
from app.api.routers.chat_event_router import router as chat_event_router
from app.api.routers.websocket_router import router as websocket_router
from app.api.routers.study_router import router as study_router
from app.api.routers.constellation import router as constellation_router
import asyncio
from app.tasks.session_task_runner import session_checker_all_users_loop
import logging
from app.models.db.user_model import User  # ✅ 반드시 추가
from app.models.db.session_log import SessionLog 
from app.models.db.session_summary import SessionSummary
from app.models.db.study_model import DiaryAnalysisReport
from transformers import AutoTokenizer , AutoModelForCausalLM
import torch
import os
from pathlib import Path
#from app.services import endtime_event
# from app.services.celery_app import summarize_task
import app.tasks.session_end_event    # ← 리스너 등록용 임포트 (이걸로 저장을 시키지 않음)
from fastapi.staticfiles import StaticFiles  # 추가 필요
from app.services.celery_app import session_summarize_task




# 기존 핸들러 초기화
for h in logging.root.handlers[:]:
    logging.root.removeHandler(h)

# 루트 로거 레벨을 DEBUG로, 출력 포맷 지정
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)

# Uvicorn 내장 로거까지 DEBUG로 바꾸기
logging.getLogger("uvicorn").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)




Base.metadata.create_all(bind=engine) # 클래스 정의생성해서 테이블 만들기


app = FastAPI()



# 🔽 이거 추가!
app.mount("/static", StaticFiles(directory="static"), name="static")



# 라우터 등록
app.include_router(register_router)
app.include_router(html_router)
app.include_router(chat_router)
app.include_router(chat_event_router)
app.include_router(websocket_router)
app.include_router(study_router)
app.include_router(constellation_router)


@app.on_event("startup")
async def startup_event():
    # 모델 로딩 제거 ✅

    # 세션 체크 백그라운드 실행
    print("🌀 전체 세션 체크 백그라운드 시작")
    asyncio.create_task(session_checker_all_users_loop())



# main.py 하단
for route in app.routes:
    print("✅ Registered route:", route.path)




