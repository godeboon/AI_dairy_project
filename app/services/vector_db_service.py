# app/services/vector_db_service.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from app.clients.huggingface_client import HuggingFaceClient
import hashlib

def _sha1_16(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]

class VectorDBService:
    """
    - 메트릭을 'cosine'으로 고정(권장)
    - 유사도 변환은 cosine일 때만 지원
    """
    def __init__(
        self,
        persist_directory: str = "D:/chroma_db",
        collection_name: str = "chat_system",
        metric: str = "cosine",  # 'cosine' | 'l2' | 'ip'
    ):
        self.metric = metric.lower().strip()
        if self.metric not in {"cosine", "l2", "ip"}:
            raise ValueError(f"Unsupported metric: {self.metric}")

        self.embedding_client = HuggingFaceClient()  # .emb (LangChain Embeddings)
        collection_metadata = {"hnsw:space": self.metric}

        self.vectorstore = Chroma(
            embedding_function=self.embedding_client.emb,
            persist_directory=persist_directory,
            collection_name=collection_name,
            collection_metadata=collection_metadata,
        )

    # ---------- ID helpers ----------
    def build_id(self, user_id: int, session_id: str, type_: str, text: str) -> str:
        """공통 doc_id 규칙 (Dense/Sparse 동일)"""
        return f"{user_id}::{session_id}::{type_}::{_sha1_16(text)}"

    # ---------- write ----------
    def add_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        *,
        doc_id: Optional[str] = None,   # ✅ doc_id 중심
        id_: Optional[str] = None,      # (deprecated) 하위호환 용도
        persist: bool = True,
    ) -> None:
        meta = dict(metadata or {})

        # 우선순위: 인자로 받은 doc_id > meta의 doc_id > (없으면 생성)
        if doc_id is None:
            doc_id = meta.get("doc_id")
        if doc_id is None:
            # 가능한 한 동일 규칙으로 생성하려면 호출 측에서 build_id 사용 권장
            # 여기서는 비상용(콜 사이트에서 이미 만들어 오는 게 정석)
            user_id = meta.get("user_id")
            session_id = meta.get("session_id")
            type_ = meta.get("type", "text")
            doc_id = self.build_id(user_id, session_id, type_, text) if all([user_id, session_id]) else _sha1_16(text)

        # 메타에도 정규화된 doc_id 넣어줌
        meta["doc_id"] = doc_id

        # (하위호환) id_가 들어와도 무시하고 doc_id를 실제 Chroma id로 사용
        doc = Document(page_content=text, metadata=meta)
        self.vectorstore.add_documents([doc], ids=[doc_id])

        if persist:
            self.vectorstore.persist()

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        *,
        doc_ids: Optional[List[str]] = None,  # ✅ doc_id 리스트
        ids: Optional[List[str]] = None,      # (deprecated)
        persist: bool = True,
    ) -> None:
        metas: List[Dict[str, Any]] = [dict(metadatas[i]) if metadatas else {} for i in range(len(texts))]

        # doc_ids 정규화
        if doc_ids is None:
            # ids(deprecated)가 오면 그대로 doc_ids로 승격
            if ids is not None:
                doc_ids = ids
            else:
                # 메타 내부 doc_id를 쓰거나, 없으면 생성
                doc_ids = []
                for i, t in enumerate(texts):
                    meta = metas[i]
                    did = meta.get("doc_id")
                    if did is None:
                        user_id = meta.get("user_id")
                        session_id = meta.get("session_id")
                        type_ = meta.get("type", "text")
                        did = self.build_id(user_id, session_id, type_, t) if all([user_id, session_id]) else _sha1_16(t)
                    meta["doc_id"] = did
                    doc_ids.append(did)
        else:
            # 주어진 doc_ids를 메타에도 반영
            for i, did in enumerate(doc_ids):
                metas[i]["doc_id"] = did

        docs = [Document(page_content=texts[i], metadata=metas[i]) for i in range(len(texts))]
        self.vectorstore.add_documents(docs, ids=doc_ids)

        if persist:
            self.vectorstore.persist()

    def upsert_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        *,
        doc_id: Optional[str] = None,   # ✅ doc_id 중심
        id_: Optional[str] = None,      # (deprecated)
        persist: bool = True,
    ) -> None:
        meta = dict(metadata or {})

        # doc_id 정규화
        if doc_id is None:
            doc_id = meta.get("doc_id")
        if doc_id is None:
            user_id = meta.get("user_id")
            session_id = meta.get("session_id")
            type_ = meta.get("type", "text")
            doc_id = self.build_id(user_id, session_id, type_, text) if all([user_id, session_id]) else _sha1_16(text)

        # 기존 삭제 후 add (Chroma는 upsert API가 없어 delete→add)
        try:
            self.vectorstore.delete(ids=[doc_id])
        except Exception:
            pass

        # 메타에도 doc_id 동기화
        meta["doc_id"] = doc_id
        self.add_document(text=text, metadata=meta, doc_id=doc_id, persist=persist)

    # ---------- 세션 단위 삭제 ----------
    def delete_by_session(self, user_id: int, session_id: str) -> int:
        try:
            self.vectorstore._collection.delete(where={"user_id": user_id, "session_id": session_id})
            self.vectorstore.persist()
            return 1
        except Exception:
            return 0

    # ---------- 존재 확인 ----------
    def exists(self, doc_id: str) -> bool:
        try:
            got = self.vectorstore._collection.get(ids=[doc_id])
            return len(got.get("ids") or []) > 0
        except Exception:
            return False

    # ---------- read ----------
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
        res = self.vectorstore.similarity_search_with_score(query, k=top_k, filter=where)

        out: List[Dict[str, Any]] = []
        for doc, dist in res:
            item = {
                "text": doc.page_content,
                "metadata": doc.metadata,
                "distance": float(dist),
            }
            if return_similarity and self.metric == "cosine":
                item["similarity"] = 1.0 - float(dist)
            out.append(item)

        if max_distance is not None:
            out = [x for x in out if x["distance"] <= max_distance]

        if min_similarity is not None:
            if self.metric != "cosine":
                raise ValueError("min_similarity는 metric='cosine'에서만 사용할 수 있습니다.")
            out = [x for x in out if (x.get("similarity") is not None and x["similarity"] >= min_similarity)]

        return out

    # ---------- utils ----------
    def info(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "collection_name": self.vectorstore._collection.name,  # type: ignore
        }
