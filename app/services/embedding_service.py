import json
import logging
from datetime import datetime
from app.services.vector_db_service import VectorDBService
from app.models.db.session_summary import GPTSessionSummary
from app.core.connection import get_db

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.vdb = VectorDBService()

    def create_session_embeddings(self, user_id: int, session_id: str):
        """세션의 summary/keywords를 임베딩 저장 → 배치 끝 persist() 한 번."""
        db = None
        try:
            logger.info("▶ EMB_START uid=%s sid=%s", user_id, session_id)

            db = next(get_db())
            rec = (
                db.query(GPTSessionSummary)
                .filter(
                    GPTSessionSummary.user_id == user_id,
                    GPTSessionSummary.session_id == session_id,
                )
                .first()
            )
            if not rec:
                logger.warning("⚠️ 세션 데이터 없음 uid=%s sid=%s", user_id, session_id)
                return

            summary: str = rec.summary or ""
            keywords_json = rec.keywords

            processed_keywords = self._preprocess_keywords(keywords_json)
            individual_keywords = self._extract_individual_keywords(keywords_json)

            base_meta = self._create_metadata(user_id, session_id)

            # --- upsert with ids=doc_id (공식 래퍼만 사용) ---
            if summary:
                doc_id = self.vdb.build_id(user_id, session_id, "summary", summary)
                self.vdb.upsert_document(text=summary, metadata={**base_meta, "type": "summary", "doc_id": doc_id}, doc_id=doc_id)

            if processed_keywords:
                doc_id = self.vdb.build_id(user_id, session_id, "keywords_all", processed_keywords)
                self.vdb.upsert_document(text=processed_keywords, metadata={**base_meta, "type": "keywords_all", "doc_id": doc_id}, doc_id=doc_id)

            for kw in individual_keywords:
                if not kw:
                    continue
                doc_id = self.vdb.build_id(user_id, session_id, "keyword", kw)
                self.vdb.upsert_document(text=kw, metadata={**base_meta, "type": "keyword", "keyword": kw, "doc_id": doc_id}, doc_id=doc_id)

            # 배치 끝 플러시(다른 프로세스에서 즉시 조회 가능하도록)
            # self.vdb.persist()
            logger.info("✅ EMB_DONE uid=%s sid=%s", user_id, session_id)

        except Exception as e:
            logger.exception("❌ EMB_FAIL uid=%s sid=%s err=%s", user_id, session_id, type(e).__name__)
            raise
        finally:
            try:
                if db is not None:
                    db.close()
            except Exception:
                pass

    # ------------- helpers -------------
    def _preprocess_keywords(self, keywords_json):
        try:
            if isinstance(keywords_json, str):
                keywords = json.loads(keywords_json)
            else:
                keywords = keywords_json or []
            return ", ".join([str(k) for k in keywords if k])
        except Exception as e:
            logger.error("❌ 키워드 전처리 실패: %s", e)
            return ""

    def _extract_individual_keywords(self, keywords_json):
        try:
            if isinstance(keywords_json, str):
                keywords = json.loads(keywords_json)
            else:
                keywords = keywords_json or []
            return [str(k) for k in keywords if k]
        except Exception as e:
            logger.error("❌ 개별 키워드 추출 실패: %s", e)
            return []

    def _create_metadata(self, user_id: int, session_id: str):
        now = datetime.now()
        return {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": now.isoformat(),
            "yymmdd": now.strftime("%y%m%d"),
        }