# app/services/sparse_service.py
import sqlite3
import hashlib
import json
from typing import Any, Dict, List, Optional

class SparseIndexService:
    """
    SQLite FTS5 기반 BM25 Sparse 검색 서비스
    - summary / key_sentence / keywords_all / keyword 색인
    - 공통 doc_id를 별도 컬럼과 meta_json 모두에 저장하여 Dense와 동일 식별 체계 유지
    """

    def __init__(self, db_path: str = "D:/chroma_db/sparse_fts.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._init_schema()

    def _init_schema(self):
        # trigram tokenizer: 한국어 대응(형태소 분석기 없이도 부분검색 유리)
        self.conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
            text,               -- 색인 본문 (summary / key_sentence / keywords_all / keyword)
            type UNINDEXED,     -- summary / key_sentence / keywords_all / keyword
            user_id UNINDEXED,
            session_id UNINDEXED,
            doc_id UNINDEXED,   -- ✅ 공통 doc_id 저장
            meta_json UNINDEXED,
            tokenize='trigram'
        );
        """)
        self.conn.commit()

    # ---------- ID 생성 (Dense와 동일 규칙) ----------
    def build_id(self, user_id: int, session_id: str, type_: str, text: str) -> str:
        sha1 = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
        return f"{user_id}::{session_id}::{type_}::{sha1}"

    # ---------- 문서 추가 ----------
    def add_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        *,
        persist: bool = True
    ) -> None:
        """
        metadata에는 반드시 다음 키가 있어야 함:
          - type, user_id, session_id, doc_id
        """
        # doc_id 없으면 안전하게 생성해서 채워 넣음
        doc_id = metadata.get("doc_id")
        if not doc_id:
            doc_id = self.build_id(metadata["user_id"], metadata["session_id"], metadata["type"], text)
            metadata = {**metadata, "doc_id": doc_id}

        self.conn.execute(
            "INSERT INTO docs_fts (text, type, user_id, session_id, doc_id, meta_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                text,
                metadata.get("type"),
                metadata.get("user_id"),
                metadata.get("session_id"),
                doc_id,
                json.dumps(metadata, ensure_ascii=False),
            ),
        )
        if persist:
            self.conn.commit()

    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        *,
        persist: bool = True
    ) -> None:
        for t, m in zip(texts, metadatas):
            self.add_document(t, m, persist=False)
        if persist:
            self.conn.commit()

    # ---------- Upsert (doc_id 기준) ----------
    def upsert_document(self, text: str, metadata: Dict[str, Any]) -> None:
        """
        동일 doc_id 행을 지우고 다시 넣는다.
        doc_id가 없으면 build_id로 생성 후 meta에 주입.
        """
        doc_id = metadata.get("doc_id")
        if not doc_id:
            # doc_id 미제공 시 안전 생성
            doc_id = self.build_id(metadata["user_id"], metadata["session_id"], metadata["type"], text)
            metadata = {**metadata, "doc_id": doc_id}

        # 기존 삭제 (doc_id 단일 키)
        self.conn.execute("DELETE FROM docs_fts WHERE doc_id=?", (doc_id,))
        # 새로 추가
        self.add_document(text, metadata)

    # ---------- 세션 단위 삭제 ----------
    def delete_by_session(self, user_id: int, session_id: str) -> None:
        self.conn.execute(
            "DELETE FROM docs_fts WHERE user_id=? AND session_id=?",
            (user_id, session_id),
        )
        self.conn.commit()

    # ---------- 검색 ----------
    def search(
        self,
        query: str,
        top_k: int = 10,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        sql = (
            "SELECT text, type, user_id, session_id, doc_id, meta_json, bm25(docs_fts) as score "
            "FROM docs_fts WHERE docs_fts MATCH ?"
        )
        params = [query]

        if user_id is not None:
            sql += " AND user_id=?"
            params.append(user_id)

        sql += " ORDER BY score LIMIT ?"
        params.append(top_k)

        cur = self.conn.execute(sql, tuple(params))
        rows = cur.fetchall()

        results: List[Dict[str, Any]] = []
        for text, type_, uid, sid, did, meta_json, score in rows:
            try:
                meta = json.loads(meta_json)
            except Exception:
                meta = {}
            results.append({
                "text": text,
                "type": type_,
                "user_id": uid,
                "session_id": sid,
                "doc_id": did,
                "metadata": meta,
                "score": score,
            })
        return results
