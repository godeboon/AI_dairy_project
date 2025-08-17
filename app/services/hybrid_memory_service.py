# app/services/hybrid_memory_service.py
from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.services.sparse_service import SparseIndexService
from app.services.vector_db_service import VectorDBService

logger = logging.getLogger(__name__)


@dataclass
class DocAgg:
    doc_id: str
    session_id: str
    user_id: int
    yymmdd: Optional[str] = None

    # 집계 스코어(Weighted RRF 기반)
    base_score: float = 0.0

    # 고유조합 카운트용
    types: set = field(default_factory=set)          # {'summary','key_sentence','keywords_all','keyword'}
    modalities: set = field(default_factory=set)     # {'sparse','dense'}
    combos: set = field(default_factory=set)         # {(type, modality)}

    # 최종 스코어와 버킷
    final_score: float = 0.0
    n_hits: int = 0
    bucket: str = "low"  # 'high' | 'middle' | 'low'


class HybridMemoryService:
    """
    하이브리드 검색(FTS5 Sparse + Chroma Dense)
    - 순위기반 결합: Weighted RRF
    - 공정성/안정성:
        · (doc_id, type, modality) 고유조합 카운트
        · 타입 다양성 보너스 / 모달리티 교차 보너스
        · 3주 이후 주당 5% 완만 감쇠 (하한 0.6)
    - 버킷:
        · High: n_hits >= 3
        · Middle: n_hits == 2
        · Low: n_hits == 1
    """

    _TOKEN_SPLIT_RE = re.compile(r"[\s\u3000]+")  # 공백류

    def __init__(
        self,
        sparse: Optional[SparseIndexService] = None,
        dense: Optional[VectorDBService] = None,
        *,
        rrf_k: int = 60,
        sparse_k: int = 200,
        dense_k: int = 50,
    ):
        self.sparse = sparse or SparseIndexService()
        self.dense = dense or VectorDBService()
        self.RRF_K = rrf_k
        self.SPARSE_K = sparse_k
        self.DENSE_K = dense_k

    # ---------------------- Public API ----------------------
    def hybrid_retrieve(
        self,
        user_query: str,
        user_id: int,
        yymmdd: str,
        top_k: int = 12,   # doc_id 집계 후 상위 N (버킷 선정용으로 넉넉히)
    ) -> List[Dict[str, Any]]:
        """
        반환(정렬: final_score desc):
        [
          {
            "doc_id": str,
            "session_id": str,
            "user_id": int,
            "yymmdd": str|None,
            "score": float,          # final_score
            "n_hits": int,
            "bucket": "high"|"middle"|"low",
            "types": list[str],
            "modalities": list[str],
          },
          ...
        ]
        """
        q = (user_query or "").strip()
        token_cnt = self._count_tokens(q)
        w_idx, w_type = self._choose_weights(token_cnt)
        logger.info(
            f"HYB_START user_id={user_id} yymmdd={yymmdd} token_cnt={token_cnt} "
            f"w_sparse={w_idx['sparse']} w_dense={w_idx['dense']} w_type={w_type}"
        )

        # 1) 인덱스별 검색
        sparse_hits = self._search_sparse(q, user_id=user_id)
        dense_hits = self._search_dense(q, user_id=user_id)

        logger.info(f"HYB_FETCH sparse_n={len(sparse_hits)} dense_n={len(dense_hits)}")

        # 2) Weighted RRF 결합(고유조합 카운팅 포함)
        fused = self._weighted_rrf_aggregate(
            sparse_hits, dense_hits, w_idx=w_idx, w_type=w_type
        )

        # 3) 보너스 + 시간감쇠 + 버킷 산정
        now = datetime.now()
        for doc in fused.values():
            self._apply_bonuses(doc)
            self._apply_time_decay(doc, now)
            self._assign_bucket(doc)

        # 4) 정렬 및 상위 추림
        docs = sorted(fused.values(), key=lambda d: d.final_score, reverse=True)[:top_k]

        # 5) 출력을 표준 dict로 변환
        out: List[Dict[str, Any]] = []
        for d in docs:
            out.append({
                "doc_id": d.doc_id,
                "session_id": d.session_id,
                "user_id": d.user_id,
                "yymmdd": d.yymmdd,
                "score": round(d.final_score, 6),
                "n_hits": d.n_hits,
                "bucket": d.bucket,
                "types": sorted(list(d.types)),
                "modalities": sorted(list(d.modalities)),
            })
        logger.info(f"HYB_TOP doc_ids={[x['doc_id'] for x in out]}")
        return out

    # ---------------------- Retrieval ----------------------
    def _search_sparse(self, q: str, *, user_id: int) -> List[Dict[str, Any]]:
        hits: List[Dict[str, Any]] = []
        try:
            raw = self.sparse.search(q, top_k=self.SPARSE_K, user_id=user_id)
            for i, h in enumerate(raw, start=1):
                meta = h.get("metadata") or {}
                typ = self._normalize_type(h.get("type") or meta.get("type"))
                doc_id, session_id, yymmdd = self._resolve_ids(meta, source="sparse", text=h.get("text", ""))

                hits.append({
                    "index": "sparse",
                    "rank": i,  # bm25 정렬 가정
                    "text": h.get("text", ""),
                    "type": typ,
                    "doc_id": doc_id,
                    "session_id": session_id,
                    "user_id": meta.get("user_id"),
                    "yymmdd": meta.get("yymmdd") or yymmdd,
                    "metadata": meta,
                })
        except Exception:
            logger.exception("HYB_ERROR sparse_search_failed")
        return hits

    def _search_dense(self, q: str, *, user_id: int) -> List[Dict[str, Any]]:
        hits: List[Dict[str, Any]] = []
        try:
            raw = self.dense.search_similar(
                q, top_k=self.DENSE_K, where={"user_id": user_id}, return_similarity=True
            )
            # similarity 내림차순
            raw = sorted(raw, key=lambda x: (x.get("similarity") is None, -(x.get("similarity") or -1e9)))
            for i, h in enumerate(raw, start=1):
                meta = h.get("metadata") or {}
                typ = self._normalize_type(meta.get("type"))
                doc_id, session_id, yymmdd = self._resolve_ids(meta, source="dense", text=h.get("text", ""))

                hits.append({
                    "index": "dense",
                    "rank": i,  # similarity 내림차순으로 부여
                    "text": h.get("text", ""),
                    "type": typ,
                    "doc_id": doc_id,
                    "session_id": session_id,
                    "user_id": meta.get("user_id"),
                    "yymmdd": meta.get("yymmdd") or yymmdd,
                    "metadata": meta,
                })
        except Exception:
            logger.exception("HYB_ERROR dense_search_failed")
        return hits

    # ---------------------- Fusion & Scoring ----------------------
    def _weighted_rrf_aggregate(
        self,
        sparse_hits: List[Dict[str, Any]],
        dense_hits: List[Dict[str, Any]],
        *,
        w_idx: Dict[str, float],
        w_type: Dict[str, float],
    ) -> Dict[str, DocAgg]:
        fused: Dict[str, DocAgg] = {}

        def add_hit(hit: Dict[str, Any]):
            doc_id = hit["doc_id"]
            session_id = hit["session_id"]
            user_id = int(hit.get("user_id") or 0)
            yymmdd = hit.get("yymmdd")

            if doc_id not in fused:
                fused[doc_id] = DocAgg(
                    doc_id=doc_id, session_id=session_id, user_id=user_id, yymmdd=yymmdd
                )

            t = hit["type"] or "unknown"
            idx = hit["index"]
            wt = w_type.get(t, 1.0)
            wi = w_idx.get(idx, 0.0)
            rank = max(1, int(hit.get("rank", 999999)))
            incr = (wi * wt) * (1.0 / (self.RRF_K + rank))

            fused[doc_id].base_score += incr

            # 고유조합 카운팅(키워드 다발 억제: (type, modality) 한 번만)
            combo = (t, idx)
            if combo not in fused[doc_id].combos:
                fused[doc_id].combos.add(combo)
                fused[doc_id].types.add(t)
                fused[doc_id].modalities.add(idx)

        for h in sparse_hits:
            add_hit(h)
        for h in dense_hits:
            add_hit(h)

        # n_hits 확정
        for d in fused.values():
            d.n_hits = len(d.combos)

        return fused

    def _apply_bonuses(self, d: DocAgg) -> None:
        """타입 다양성/모달리티 교차 보너스 + 최종(base+bonus) 계산(감쇠 전)"""
        unique_types = len(d.types)
        bonus_type = 0.05 * max(0, unique_types - 1)   # 최대 0.15
        if bonus_type > 0.15:
            bonus_type = 0.15

        bonus_mod = 0.07 if (("sparse" in d.modalities) and ("dense" in d.modalities)) else 0.0
        pre_decay = d.base_score + bonus_type + bonus_mod
        d.final_score = pre_decay  # 감쇠는 별도 단계에서

    def _apply_time_decay(self, d: DocAgg, now: datetime) -> None:
        """
        3주(21일) 그레이스: 감쇠 0
        이후 주당 5% 곱셈 감쇠, 하한 0.6
        세션 시점은 yymmdd만 사용. 없으면 감쇠 미적용.
        """
        ymd = d.yymmdd or (d.session_id.split("_")[0] if d.session_id else None)
        if not ymd or len(ymd) != 6:
            return

        # yymmdd -> datetime (2000~2099 가정)
        yy = int(ymd[:2])
        mm = int(ymd[2:4])
        dd = int(ymd[4:6])
        year = 2000 + yy
        try:
            dt = datetime(year, mm, dd)
        except Exception:
            return

        age_days = (now.date() - dt.date()).days
        if age_days <= 21:
            decay = 1.0
        else:
            weeks_over = max(0, (age_days - 21) // 7)
            decay = (0.95) ** weeks_over
            if decay < 0.6:
                decay = 0.6

        d.final_score *= decay

    def _assign_bucket(self, d: DocAgg) -> None:
        if d.n_hits >= 3:
            d.bucket = "high"
        elif d.n_hits == 2:
            d.bucket = "middle"
        else:
            d.bucket = "low"

    # ---------------------- Utils ----------------------
    def _count_tokens(self, q: str) -> int:
        if not q:
            return 0
        toks = [t for t in self._TOKEN_SPLIT_RE.split(q) if t]
        return len(toks)

    def _choose_weights(self, token_cnt: int) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        인덱스 가중치 + 타입 가중치
        - 인덱스: {'sparse': w, 'dense': w}
        - 타입: {'summary','key_sentence','keywords_all','keyword'}
        """
        if token_cnt <= 2:
            w_idx = {"sparse": 0.75, "dense": 0.25}
            w_type = {"summary": 0.3, "key_sentence": 0.4, "keywords_all": 0.7, "keyword": 1.0}
        elif token_cnt <= 6:
            w_idx = {"sparse": 0.60, "dense": 0.40}
            w_type = {"summary": 0.5, "key_sentence": 0.6, "keywords_all": 0.8, "keyword": 0.9}
        elif token_cnt <= 20:
            w_idx = {"sparse": 0.45, "dense": 0.55}
            w_type = {"summary": 0.8, "key_sentence": 0.9, "keywords_all": 0.6, "keyword": 0.4}
        else:
            w_idx = {"sparse": 0.30, "dense": 0.70}
            w_type = {"summary": 1.0, "key_sentence": 0.8, "keywords_all": 0.5, "keyword": 0.2}
        return w_idx, w_type

    def _normalize_type(self, t: Optional[str]) -> str:
        """
        저장 계층의 다양한 표기 → 표준형으로 정규화
        - 'keywords' → 'keywords_all'
        - 'individual_keyword' → 'keyword'
        - 없는 경우 'unknown'
        """
        if not t:
            return "unknown"
        t = str(t).strip().lower()
        if t == "keywords":
            return "keywords_all"
        if t == "individual_keyword":
            return "keyword"
        return t

    def _resolve_ids(self, meta: Dict[str, Any], *, source: str, text: str) -> Tuple[str, str, Optional[str]]:
        """
        doc_id, session_id, yymmdd 해석
        - 메타에 doc_id 없으면 doc_id = f"{user_id}:{session_id}"
        - session_id 없으면 source 기반 fallback 키 합성(희소 사례)
        """
        user_id = str(meta.get("user_id", "u"))
        session_id = str(meta.get("session_id", "")) or "s"
        yymmdd = meta.get("yymmdd")

        if meta.get("doc_id"):
            doc_id = str(meta["doc_id"])
        else:
            # 세션 단위 doc_id를 기본으로(동일 세션 묶임)
            doc_id = f"{user_id}:{session_id}"

        return doc_id, session_id, yymmdd
