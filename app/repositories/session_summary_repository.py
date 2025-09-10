from sqlalchemy.orm import Session
from app.models.db.session_summary import SessionSummary
from app.models.db.user_model import User
from app.models.db.session_log import SessionLog

class SessionSummaryRepository:
    """
    [데이터접근/저장]
    - 이미 요약이 있으면 exists()로 체크
    - save()로 새 요약을 DB에 커밋
    """

    def __init__(self, db: Session):
        self.db = db

    def exists(self, user_id: int, session_id: str) -> bool:
        return (
            self.db.query(SessionSummary)
                   .filter_by(user_id=user_id, session_id=session_id)
                   .first() is not None
        )

    def save(self, user_id: int, session_id: str, summary_text: str):
        summary = SessionSummary(
            user_id=user_id,
            session_id=session_id,
            summary=summary_text
        )
        self.db.add(summary)
        self.db.commit() 