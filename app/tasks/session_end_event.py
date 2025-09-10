print("▶ endtime_event 모듈 로드됨")

import logging
from celery import chain
from sqlalchemy import inspect, event

from app.models.db.session_log import SessionLog
from app.services.celery_app import (
    session_summarize_task,
    session_embed_task,
)
# 필요 시: mark_embeddings_ready_task 도 여기서 import 가능

logger = logging.getLogger(__name__)


@event.listens_for(SessionLog, "after_update")
def on_session_end(mapper, conn, target: SessionLog):
    """
    SessionLog.end_time 이 None -> 값 으로 바뀌는 '최초 종료 확정' 순간에만 트리거.
    요약 → 임베딩 순서 보장.
    """
    hist = inspect(target).attrs.end_time.history

    # 과거 None 이고 새 값이 생겼을 때만 동작
    if (
        hist.has_changes()
        and hist.deleted and hist.deleted[0] is None
        and hist.added and hist.added[0] is not None
    ):
        user_id = target.user_id
        session_id = target.session_id

        logger.info(
            "on_session_end 트리거: user_id=%s, session_id=%s, end_time=%s",
            user_id, session_id, target.end_time
        )

        try:
            # ✅ 순서 보장: 요약 → 임베딩 (요약 완료 후 임베딩 시작)
            session_summarize_task.delay(user_id=user_id, session_id=session_id)

            logger.info(
                "세션 종료 태스크 디스패치 완료: user_id=%s, session_id=%s",
                user_id, session_id
            )
        except Exception as e:
            logger.exception(
                "세션 종료 체인 디스패치 실패: user_id=%s, session_id=%s, err=%s",
                user_id, session_id, e
            )