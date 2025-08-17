from sqlalchemy.orm import Session
from app.models.db.chat_message_model import ChatMessage

class ChatMessageRepository:
    """
    [데이터접근/조회]
    - user_id, session_id로 메시지 리스트를 timestamp 순으로 반환
    """

    def __init__(self, db: Session):
        self.db = db

    def list_by_session(self, user_id: int, session_id: str):
        return (
            self.db.query(ChatMessage)
                   .filter_by(user_id=user_id, session_id=session_id)
                   .order_by(ChatMessage.timestamp)
                   .all()
        ) 