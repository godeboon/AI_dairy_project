# app/services/vector_db_service.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence
import logging
import json
from chromadb.errors import InternalError  # 파일 상단에 추가
from langchain_chroma import Chroma  # ← 혼용 방지: langchain_chroma로 통일
from langchain.schema import Document
from app.clients.huggingface_client import HuggingFaceClient  # 내부에서 langchain_huggingface 사용 OK
from datetime import datetime
import time
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config.settings import settings

logger = logging.getLogger(__name__)


def _local_time_fields() -> Dict[str, Any]:
    now = datetime.now()
    # 로컬 서버 시간 문자열 + epoch(ms)
    return {
        "local_time": now.strftime("%Y-%m-%d %H:%M:%S.%f %z"),
        "epoch_ms": int(now.timestamp() * 1000),
    }

class VectorDBService:
    """
    - HNSW metric 고정(컬렉션 생성 시 반영)
    - 공식 래퍼만 사용 (delete: vectorstore.delete, add: vectorstore.add_documents)
    - ids=doc_id 일관 유지, 메타데이터에도 doc_id 저장
    - 배치 끝 persist(), 조회는 실패 시 자동 reload() 후 재시도
    """
    def __init__(
        self,
        *,
        persist_directory: str = settings.chroma_path,
        collection_name: str = "chat_system",
        metric: str = "cosine",  # 'cosine' | 'l2' | 'ip'
    ):
        self._persist_directory = persist_directory
        self._collection_name = collection_name
        self.metric = metric.lower().strip()
        if self.metric not in {"cosine", "l2", "ip"}:
            raise ValueError(f"Unsupported metric: {self.metric}")

        self._emb = HuggingFaceClient().emb  # langchain_huggingface.HuggingFaceEmbeddings
        self._open()
        logger.debug(
            "VDB_INIT_DONE collection=%s metric=%s",
            self._collection_name, self.metric
        )

    # ---------- lifecycle ----------
    def _open(self) -> None:
        if settings.chroma_host:
            # 서버 모드: HttpClient로 접속
            client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                settings=ChromaSettings(allow_reset=settings.chroma_allow_reset),
            )
            self.vectorstore = Chroma(
                client=client,
                embedding_function=self._emb,
                collection_name=self._collection_name,
                collection_metadata={"hnsw:space": self.metric},
            )
            logger.info(
                "VDB_OPEN_SERVER host=%s port=%s collection=%s metric=%s",
                settings.chroma_host,
                settings.chroma_port,
                self._collection_name,
                self.metric,
            )
        else:
            # 파일 모드: 기존 경로 사용
            self.vectorstore = Chroma(
                embedding_function=self._emb,
                persist_directory=self._persist_directory,
                collection_name=self._collection_name,
                collection_metadata={"hnsw:space": self.metric},
            )
            logger.info(
                "VDB_OPEN_FILE path=%s collection=%s metric=%s",
                self._persist_directory,
                self._collection_name,
                self.metric,
            )

    def reload(self) -> None:
        """reset 금지. 새 핸들로 재오픈."""
        logger.info("VDB_RELOAD_START collection=%s", self._collection_name)
        self._open()
        logger.info("VDB_RELOAD_OK collection=%s", self._collection_name)

    def persist(self) -> None:
        try:
            # 서버 모드에서는 persist가 필요 없을 수 있음. 호출은 안전하게 시도만.
            self.vectorstore.persist()
            logger.debug("VDB_PERSIST_OK collection=%s", self._collection_name)
        except Exception as e:
            logger.debug("VDB_PERSIST_SKIP collection=%s err=%s", self._collection_name, type(e).__name__)

    # ---------- id helper ----------
    def build_id(self, user_id: int, session_id: str, type_: str, text: str) -> str:
        import hashlib
        doc_id = f"{user_id}::{session_id}::{type_}::{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"
        try:
            f = _local_time_fields()
            logger.info(
                "ID_GEN uid=%s sid=%s typ=%s doc_id=%s text_len=%s local_time=%s epoch_ms=%s",
                user_id,
                session_id,
                type_,
                doc_id,
                len(text or ""),
                f.get("local_time"),
                f.get("epoch_ms"),
            )
        except Exception:
            logger.debug("ID_GEN_LOG_SKIP")
        return doc_id

    # ---------- write ----------
    def add_document(self, *, text: str, metadata: Optional[Dict[str, Any]] = None, doc_id: Optional[str] = None) -> None:
        meta = dict(metadata or {})
        if doc_id:
            meta["doc_id"] = doc_id
        doc = Document(page_content=text, metadata=meta)
        # 임베딩 호출/저장 타이밍 측정 및 로컬시간 로깅
        _f = _local_time_fields()
        logger.info(
            "EMB_ADD_START doc_id=%s provider=%s local_time=%s epoch_ms=%s",
            doc_id,
            type(self._emb).__name__,
            _f.get("local_time"),
            _f.get("epoch_ms"),
        )
        _t0 = datetime.now().timestamp()
        try:
            self.vectorstore.add_documents([doc], ids=([doc_id] if doc_id else None))
        except Exception:
            _f2 = _local_time_fields()
            logger.exception(
                "EMB_ADD_ERROR doc_id=%s local_time=%s epoch_ms=%s",
                doc_id,
                _f2.get("local_time"),
                _f2.get("epoch_ms"),
            )
            raise
        _dur_ms = int((datetime.now().timestamp() - _t0) * 1000)
        _f3 = _local_time_fields()
        logger.info(
            "EMB_ADD_OK doc_id=%s duration_ms=%s local_time=%s epoch_ms=%s",
            doc_id,
            _dur_ms,
            _f3.get("local_time"),
            _f3.get("epoch_ms"),
        )
        logger.debug("VDB_ADD_ONE_OK doc_id=%s", doc_id)

    def add_documents(
        self,
        *,
        texts: Sequence[str],
        metadatas: Optional[Sequence[Dict[str, Any]]] = None,
        ids: Optional[Sequence[str]] = None,
    ) -> None:
        docs: List[Document] = []
        for i, t in enumerate(texts):
            meta = dict(metadatas[i]) if metadatas else {}
            if ids and ids[i]:
                meta["doc_id"] = ids[i]
            docs.append(Document(page_content=t, metadata=meta))
        self.vectorstore.add_documents(docs, ids=list(ids) if ids else None)
        logger.debug("VDB_ADD_BATCH_OK count=%s", len(docs))

    def upsert_document(self, *, text: str, metadata: Optional[Dict[str, Any]] = None, doc_id: str) -> None:
        """Chroma에 네이티브 upsert는 없으므로 delete(ids) → add_documents(ids)로 구현 (공식 래퍼만 사용)."""
        _f = _local_time_fields()
        logger.info(
            "VDB_UPSERT_ATTEMPT doc_id=%s local_time=%s epoch_ms=%s",
            doc_id,
            _f.get("local_time"),
            _f.get("epoch_ms"),
        )
        _t0 = datetime.now().timestamp()
        try:
            # 존재해도 에러 없이 삭제되도록 시도
            self.vectorstore.delete(ids=[doc_id])
            logger.debug("VDB_UPSERT_DEL_OK doc_id=%s", doc_id)
        except Exception as e:
            # 없는 경우 등은 경고만
            logger.debug("VDB_UPSERT_DEL_SKIP doc_id=%s err=%s", doc_id, type(e).__name__)
        try:
            self.add_document(text=text, metadata=metadata, doc_id=doc_id)
            # 쓰기 직후 flush로 읽기 레이스 완화
            try:
                self.persist()
            except Exception:
                logger.debug("VDB_UPSERT_PERSIST_SKIP doc_id=%s", doc_id)
        except Exception:
            _f_err = _local_time_fields()
            logger.exception(
                "VDB_UPSERT_ERROR doc_id=%s local_time=%s epoch_ms=%s",
                doc_id,
                _f_err.get("local_time"),
                _f_err.get("epoch_ms"),
            )
            raise
        _dur_ms = int((datetime.now().timestamp() - _t0) * 1000)
        _f2 = _local_time_fields()
        logger.info(
            "VDB_UPSERT_ADD_OK doc_id=%s duration_ms=%s local_time=%s epoch_ms=%s",
            doc_id,
            _dur_ms,
            _f2.get("local_time"),
            _f2.get("epoch_ms"),
        )

    # ---------- read ----------
    def _query_impl(self, query: str, top_k: int, where: Optional[Dict[str, Any]]):
        # LangChain Chroma: returns List[Tuple[Document, distance]]
        return self.vectorstore.similarity_search_with_score(query, k=top_k, filter=where)

    def search_similar(
        self,
        query: str,
        top_k: int = 10,
        where: Optional[Dict[str, Any]] = None,
        *,
        return_similarity: bool = False,
        max_distance: Optional[float] = None,
        min_similarity: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """'Error finding id' 유형에서만 1회 reload() 후 재시도."""
        _f_start = _local_time_fields()
        logger.info(
            "VDB_SEARCH_START k=%s where=%s local_time=%s epoch_ms=%s",
            top_k,
            json.dumps(where, ensure_ascii=False) if where is not None else "null",
            _f_start.get("local_time"),
            _f_start.get("epoch_ms"),
        )
        _t0 = datetime.now().timestamp()
        # where 감사 로깅: 빈 $in/$nin 여부 포함
        try:
            in_empty = sum(
                1 for v in (where or {}).values()
                if isinstance(v, dict) and "$in" in v and isinstance(v.get("$in"), list) and len(v.get("$in", [])) == 0
            )
            nin_empty = sum(
                1 for v in (where or {}).values()
                if isinstance(v, dict) and "$nin" in v and isinstance(v.get("$nin"), list) and len(v.get("$nin", [])) == 0
            )
            coll_name = getattr(self.vectorstore, "_collection", None).name if hasattr(self.vectorstore, "_collection") else self._collection_name
            logger.debug(
                "WHERE_AUDIT collection=%s top_k=%s in_empty=%s nin_empty=%s where=%s",
                coll_name,
                top_k,
                in_empty,
                nin_empty,
                json.dumps(where, ensure_ascii=False) if where is not None else "null",
            )
        except Exception:
            logger.exception("WHERE_AUDIT_LOG_FAIL")
        def _do():
            return self._query_impl(query, top_k, where)

        try:
            res = _do()
        except InternalError as e:
            msg = str(e)
            if "Error finding id" in msg or "not found" in msg.lower():
                # 첫 시도 실패: reload 후 짧은 백오프 재시도
                logger.warning("VDB_QUERY_IDMISS err=%s → reload & retry", msg)
                self.reload()
                time.sleep(0.15)
                try:
                    res = _do()
                except InternalError as e2:
                    msg2 = str(e2)
                    if "Error finding id" in msg2 or "not found" in msg2.lower():
                        # 두 번째도 실패: 핸들 재오픈(soft reset) 후 최종 재시도
                        logger.warning("VDB_QUERY_IDMISS_2 err=%s → reopen & retry", msg2)
                        try:
                            self._open()
                        except Exception:
                            logger.debug("VDB_HANDLE_REOPEN_FAIL")
                        time.sleep(0.15)
                        res = _do()
                    else:
                        raise
            else:
                raise
        except Exception:
            _f_err = _local_time_fields()
            logger.exception(
                "VDB_SEARCH_ERROR local_time=%s epoch_ms=%s",
                _f_err.get("local_time"),
                _f_err.get("epoch_ms"),
            )
            raise

        out: List[Dict[str, Any]] = []
        for doc, dist in res:
            item = {"text": doc.page_content, "metadata": doc.metadata, "distance": float(dist)}
            if return_similarity and self.metric == "cosine":
                item["similarity"] = 1.0 - float(dist)
            out.append(item)

        if max_distance is not None:
            out = [x for x in out if x["distance"] <= max_distance]
        if min_similarity is not None:
            if self.metric != "cosine":
                raise ValueError("min_similarity는 metric='cosine'에서만 사용할 수 있습니다.")
            out = [x for x in out if (x.get("similarity") is not None and x["similarity"] >= min_similarity)]

        _dur_ms = int((datetime.now().timestamp() - _t0) * 1000)
        _f_end = _local_time_fields()
        logger.info(
            "VDB_SEARCH_OK hits=%s duration_ms=%s local_time=%s epoch_ms=%s",
            len(out),
            _dur_ms,
            _f_end.get("local_time"),
            _f_end.get("epoch_ms"),
        )
        return out


    # ---------- utils ----------
    def info(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "collection_name": getattr(self.vectorstore, "_collection", None).name if hasattr(self.vectorstore, "_collection") else self._collection_name,
        }