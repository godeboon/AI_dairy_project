import asyncio
from datetime import timedelta, datetime
from sqlalchemy.orm import Session as DBSession
from app.models.db.session_log import SessionLog
from app.models.db.chat_message_model import ChatMessage


def check_and_close_expired_sessions_for_user(db: DBSession, user_id: int):
    now = datetime.now()  # 시스템 로컬 시간 사용 (KST)

    open_sessions = (
        db.query(SessionLog)
          .filter(SessionLog.user_id == user_id, SessionLog.end_time == None)
          .all()
    )

    for session in open_sessions:
        last_chat = (
            db.query(ChatMessage)
              .filter(ChatMessage.session_id == session.session_id)
              .order_by(ChatMessage.timestamp.desc())
              .first()
        )
        if not last_chat:
            continue

        # 20분 경과 시 세션 종료
        if now - last_chat.timestamp > timedelta(minutes=3):
            session.end_time = last_chat.timestamp + timedelta(minutes=3)
            db.commit()
            print(f"[✅ 세션 종료됨] user_id={user_id}, session_id={session.session_id}")


async def session_checker_all_users_loop():
    from app.core.connection import SessionLocal
    db = SessionLocal()
    try:
        while True:
            print("🌀 전체 세션 체크 실행중")
            # 열린 세션이 있는 모든 유저 ID 조회
            user_ids = (
                db.query(SessionLog.user_id)
                  .filter(SessionLog.end_time == None)
                  .distinct()
                  .all()
            )
            for (user_id,) in user_ids:
                check_and_close_expired_sessions_for_user(db, user_id)
            await asyncio.sleep(90)  # 2분
    finally:
        db.close()
