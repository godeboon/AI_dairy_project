# app/services/embedding_service.py
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional

from app.services.vector_db_service import VectorDBService
from app.models.db.session_summary import GPTSessionSummary
from app.core.connection import get_db

# ✅ Sparse 인덱스
from app.services.sparse_service import SparseIndexService

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    GPTSessionSummary → Chroma(Dense) & SQLite FTS5(Sparse) 동시 인덱싱 서비스
    저장 단위(type):
      - "summary"       : 400자 요약문 1개
      - "key_sentence"  : 핵심 문장 1~2개
      - "keywords_all"  : 키워드 전체 문자열
      - "keyword" (×N)  : 개별 키워드
    """
    def __init__(
        self,
        vector_service: Optional[VectorDBService] = None,
        sparse_service: Optional[SparseIndexService] = None
    ):
        self.vdb = vector_service or VectorDBService()
        self.sparse = sparse_service or SparseIndexService()

    # ---------- Public ----------
    def create_session_embeddings(self, user_id: int, session_id: str) -> Dict[str, Any]:
        db = None
        try:
            logger.info(f"▶ 임베딩 시작: user_id={user_id}, session_id={session_id}")

            # 1) DB 조회
            db = next(get_db())
            row: GPTSessionSummary | None = db.query(GPTSessionSummary).filter(
                GPTSessionSummary.user_id == user_id,
                GPTSessionSummary.session_id == session_id
            ).first()

            if not row:
                return {"ok": False, "reason": "no_session_row"}

            summary_text = (row.summary or "").strip()
            key_sentence_text = (getattr(row, "key_sentence", "") or "").strip()
            keywords_raw = getattr(row, "keywords", [])

            # 2) 키워드 정규화
            keywords: List[str] = self._as_list(keywords_raw)
            keywords_all_text: str = self._join_keywords_lines(keywords)
            keywords_all_human: str = self._join_keywords_human(keywords)

            # 3) 공통 메타
            base_meta = self._base_metadata(user_id, session_id)

            # 4) 업서트 대상: (text, meta, doc_id)
            upserts: List[Tuple[str, Dict[str, Any], str]] = []

            if summary_text:
                did = self.vdb.build_id(user_id, session_id, "summary", summary_text)
                meta = {**base_meta, "type": "summary", "doc_id": did}
                upserts.append((summary_text, meta, did))

            if key_sentence_text:
                did = self.vdb.build_id(user_id, session_id, "key_sentence", key_sentence_text)
                meta = {**base_meta, "type": "key_sentence", "doc_id": did}
                upserts.append((key_sentence_text, meta, did))

            if keywords_all_text:
                did = self.vdb.build_id(user_id, session_id, "keywords_all", keywords_all_text)
                meta = {
                    **base_meta,
                    "type": "keywords_all",
                    "keywords_all": keywords_all_human,
                    "doc_id": did
                }
                upserts.append((keywords_all_text, meta, did))

            for k in keywords:
                k = k.strip()
                if not k:
                    continue
                did = self.vdb.build_id(user_id, session_id, "keyword", k)
                meta = {**base_meta, "type": "keyword", "keyword": k, "doc_id": did}
                upserts.append((k, meta, did))

            # 5) Dense + Sparse 동시 업서트
            ids: List[str] = []
            for text, meta, doc_id in upserts:
                # Dense(Chroma)
                self.vdb.upsert_document(text=text, metadata=meta, doc_id=doc_id, persist=False)
                # Sparse(FTS5)
                self.sparse.upsert_document(text=text, metadata=meta)
                ids.append(doc_id)

            # Dense persist
            try:
                self.vdb.vectorstore.persist()
            except Exception:
                pass

            logger.info(f"✅ 임베딩 완료: user_id={user_id}, session_id={session_id}, count={len(ids)}")
            return {"ok": True, "count": len(ids), "ids": ids}

        except Exception as e:
            logger.exception("❌ 임베딩 실패")
            return {"ok": False, "reason": "exception", "error": str(e)}
        finally:
            if db:
                db.close()

    # ---------- Helpers ----------
    def _as_list(self, keywords_json_or_list) -> List[str]:
        try:
            if isinstance(keywords_json_or_list, list):
                return [str(x).strip() for x in keywords_json_or_list if str(x).strip()]
            if isinstance(keywords_json_or_list, str):
                s = keywords_json_or_list.strip()
                if s.startswith("[") and s.endswith("]"):
                    arr = json.loads(s)
                    return [str(x).strip() for x in arr if str(x).strip()]
                if "," in s:
                    return [t.strip() for t in s.split(",") if t.strip()]
                return [s] if s else []
        except Exception:
            logger.warning("keywords 파싱 실패", exc_info=True)
        return []

    def _join_keywords_lines(self, keywords: List[str]) -> str:
        return "\n".join(keywords) if keywords else ""

    def _join_keywords_human(self, keywords: List[str]) -> str:
        return ", ".join(keywords) if keywords else ""

    def _base_metadata(self, user_id: int, session_id: str) -> Dict[str, Any]:
        now = datetime.now()
        return {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": now.isoformat(timespec="seconds"),
            "yymmdd": now.strftime("%y%m%d"),
        }
