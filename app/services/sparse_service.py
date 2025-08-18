# app/services/sparse_service.py
import sqlite3
import hashlib
import json
import time
import threading
from typing import Any, Dict, List, Optional

# ✅ 전역 쓰기 락 (쓰기 구간 최소 보호)
_SPARSE_WRITE_LOCK = threading.Lock()


class SparseIndexService:
    """
    SQLite FTS5 기반 BM25 Sparse 검색 서비스
    - summary / key_sentence / keywords_all / keyword 색인
    - 공통 doc_id를 별도 컬럼과 meta_json 모두에 저장하여 Dense와 동일 식별 체계 유지
    """

    def __init__(self, db_path: str = "D:/chroma_db/sparse_fts.db"):
        # 한 커넥션을 여러 스레드에서 쓰기 위해 check_same_thread=False
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        # ✅ 잠금 경합 시 대기 시간 (ms 단위가 아니라 ms*? 아님; SQLite에선 ms가 아니라 ms/?? → 파이썬에선 ms가 아닌 ms 단위로 보내도 내부적으로 ms로 처리)
        #   -> SQLite는 busy_timeout 값을 밀리초(ms)로 받음. 파이썬 sqlite3는 정수 ms 전달.
        self.conn.execute("PRAGMA busy_timeout=2000;")   # 2초 대기
        # ✅ WAL: 동시 읽기 성능/안정성 향상
        self.conn.execute("PRAGMA journal_mode=WAL;")
        # (선택) 디스크 동기화 레벨 완화: 속도/안정성 타협 (원하면 주석 해제)
        # self.conn.execute("PRAGMA synchronous=NORMAL;")
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

        # ✅ 짧은 쓰기 구간만 전역 락으로 보호
        with _SPARSE_WRITE_LOCK:
            # 짧은 트랜잭션으로 DELETE→INSERT 원자화
            # BEGIN IMMEDIATE는 바로 쓰기 락을 요청하므로 경합 시 busy_timeout 규칙대로 대기
            self.conn.execute("BEGIN IMMEDIATE;")
            try:
                # 기존 삭제 (doc_id 단일 키)
                self.conn.execute("DELETE FROM docs_fts WHERE doc_id=?", (doc_id,))
                # 새로 추가 (persist=False로, 동일 트랜잭션 내에서 처리)
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
                self.conn.commit()
            except Exception:
                # 실패 시 롤백 안전장치
                self.conn.rollback()
                raise

    # ---------- 세션 단위 삭제 ----------
    def delete_by_session(self, user_id: int, session_id: str) -> None:
        # ✅ 세션 단위 대량 삭제도 짧은 트랜잭션 + 락
        with _SPARSE_WRITE_LOCK:
            self.conn.execute("BEGIN IMMEDIATE;")
            try:
                self.conn.execute(
                    "DELETE FROM docs_fts WHERE user_id=? AND session_id=?",
                    (user_id, session_id),
                )
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

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

        # ✅ 드문 'database is locked' 방어: 짧은 재시도(80~150ms) 2회
        attempts = 3
        backoffs = [0.08, 0.12]

        last_exc: Optional[Exception] = None
        for i in range(attempts):
            try:
                cur = self.conn.execute(sql, tuple(params))
                rows = cur.fetchall()
                break
            except sqlite3.OperationalError as e:
                # 잠금 관련일 때만 재시도
                msg = str(e).lower()
                if ("database is locked" in msg or "database schema is locked" in msg) and i < attempts - 1:
                    time.sleep(backoffs[i] if i < len(backoffs) else backoffs[-1])
                    last_exc = e
                    continue
                raise
        else:
            if last_exc:
                raise last_exc

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
