from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.db.session_log import SessionLog
from app.models.db.chat_message_model import ChatMessage


def get_or_create_session_id(db: Session, user_id: int) -> str:
    now = datetime.now()  # 시스템 로컬 시간 사용 (KST)
    
    print(f"🧪 [디버깅] now type: {type(now)}")
    print(f"🧪 [디버깅] now: {now}")
    print(f"🧪 [디버깅] now.tzinfo: {now.tzinfo}")

    # 유저의 마지막 채팅 조회
    last_chat = (
        db.query(ChatMessage)
          .filter(ChatMessage.user_id == user_id)
          .order_by(ChatMessage.timestamp.desc())
          .first()
    )

    if last_chat:
        print(f"🧪 [세션체크] now: {now}")
        last_chat_timestamp = last_chat.timestamp  # 이미 timezone-naive
        print(f"🧪 [세션체크] 차이: {now - last_chat_timestamp}")
        print(f"🧪 [세션체크] last_chat.session_id: {last_chat.session_id}")

    # 20분 이내면 기존 세션 유지
    if last_chat and now - last_chat_timestamp < timedelta(minutes=3):
        print(f"✅ get_or_create_session_id: 기존 세션 유지- session_id={last_chat.session_id} ")
        return last_chat.session_id

    # 20분 초과 or 첫 메시지면 새 세션 생성
    new_session_id = generate_new_session_id(db, user_id)
    new_session = SessionLog(
        user_id=user_id,
        session_id=new_session_id,
        start_time=now  # 이미 KST로 설정됨
    )
    db.add(new_session)
    db.commit()
    print(f"✅ get_or_create_session_id: 새 세션 생성 완료 - session_id={new_session_id}")
    return new_session_id


def generate_new_session_id(db: Session, user_id: int) -> str:
    # 오늘 날짜를 YYMMDD 형식으로 추출 (KST 기준)
    today_str = datetime.now().strftime("%y%m%d")

    # 오늘 생성된 해당 유저의 세션 수 카운트
    session_count = (
        db.query(SessionLog)
          .filter(
              SessionLog.user_id == user_id,
              SessionLog.session_id.like(f"{today_str}_%")
          )
          .count()
    )

    # 다음 번호 부여 (시작은 1 → 001)
    next_number = session_count + 1
    session_id = f"{today_str}_{next_number:03d}"

    print("✅ generate new session id : 세션아이디 생성기(yymmdd)")
    return session_id
