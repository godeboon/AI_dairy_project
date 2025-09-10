from celery.utils.log import get_task_logger
from app.services.celery_app import celery
from app.models.db.session_log import SessionLog
import app.models


logger = get_task_logger(__name__)

@celery.task(bind=True, autoretry_for=(Exception,), max_retries=5, retry_backoff=True)
def session_summarize_task(self, user_id: int, session_id: str):
    logger.info(f"▶ session_summarize_task 시작: user_id={user_id}, session_id={session_id}")
    try:
        # service 정해지면 적겠음
        # service = GPTSessionSummaryService()
        # service.create_session_summary(user_id, session_id)
        logger.info(f"✅ session_summarize_task 완료: user_id={user_id}, session_id={session_id}")
    except Exception as exc:
        logger.exception(f"❌ session_summarize_task 실패, 재시도 준비 중: user_id={user_id}, session_id={session_id}")
        raise self.retry(exc=exc)

