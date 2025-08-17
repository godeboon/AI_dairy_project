from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.db.chat_event_model import ChatEvent
from app.core.connection import get_db
from app.api.dependencies.auth_dependencies import get_current_user
from app.models.db.user_model import User

from datetime import datetime

router = APIRouter(tags=["chat-event"])

@router.post("/chat/open")
def chat_open(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    evt = ChatEvent(
        user_id=current_user.id, 
        event_type="open",
        timestamp=datetime.now()  # 시스템 로컬 시간 사용 (KST)
    )
    db.add(evt)
    db.commit()
    print( "✏️chat open 로그 기록 성공")
    return {"message": "chat open logged"}

@router.post("/chat/close")
def chat_close(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    evt = ChatEvent(
        user_id=current_user.id, 
        event_type="close",
        timestamp=datetime.now()  # 시스템 로컬 시간 사용 (KST)
    )
    db.add(evt)
    db.commit()
    print( "✏️chat close 로그 기록 성공")
    return {"message": "chat close logged"}
