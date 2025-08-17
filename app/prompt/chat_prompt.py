# app/services/gpt_prompt.py
from __future__ import annotations
import unicodedata
import re
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.db.chat_message_model import ChatMessage
from app.models.db.session_summary import GPTSessionSummary
from app.services.hybrid_memory_service import HybridMemoryService
from sqlalchemy import and_, or_
from app.models.db.chat_message_model import ChatMessage
from app.models.db.session_summary import GPTSessionSummary
from sqlalchemy import case



# -------------------- 전처리 유틸 --------------------
_EMOJI_RE = re.compile(
    "["                       # 대표 이모지 블록들 제거
    "\U0001F600-\U0001F64F"   # emoticons
    "\U0001F300-\U0001F5FF"   # symbols & pictographs
    "\U0001F680-\U0001F6FF"   # transport & map
    "\U0001F1E0-\U0001F1FF"   # flags
    "\u2600-\u27BF"           # misc symbols
    "]+", flags=re.UNICODE
)

def _preprocess_query(q: str) -> str:
    if not q:
        return ""
    # 1) 정규화 + 소문자
    s = unicodedata.normalize("NFKC", q).strip().lower()
    # 2) 이모지/variation selector 제거
    s = _EMOJI_RE.sub(" ", s).replace("\ufe0f", " ")
    # 3) 웃음/울음/연타 제거 (2회 이상 반복 컷)
    s = re.sub(r"([ㅋㅎㅜㅠㅡ])\1{1,}", " ", s)
    # 4) 문장부호/기타 기호 공백화 (영문/한글/숫자 외 제거)
    s = re.sub(r"[^0-9A-Za-z가-힣\s]", " ", s)
    # 5) 영문/한글 토큰만 유지 (숫자 섞인 토큰 drop: h2h2 등)
    toks = re.findall(r"[A-Za-z가-힣]+", s)
    # 6) 공백 정리
    cleaned = " ".join(toks)
    return cleaned

# -------------------- 버킷 선별 규칙 --------------------
def _select_sessions_by_bucket(rows: List[Dict[str, Any]], need: int = 4) -> Dict[str, List[Dict[str, Any]]]:
    """
    rows: hybrid_retrieve 결과(final_score desc 정렬 가정 X → 내부에서 정렬)
    규칙:
      - 원칙: High 1, Middle 1, Low 2 = 4
      - 예외: High가 4개 이상이면 High 4
      - 부족 시 상하 버킷에서 점수순 보충, 항상 need개 맞추기 (불가하면 있는 만큼)
    반환: {"high": [...], "middle": [...], "low": [...], "picked": [...]}  # picked는 최종 4개 모음
    """
    # 정렬
    rows = sorted(rows, key=lambda r: r["score"], reverse=True)

    high = [r for r in rows if r["bucket"] == "high"]
    mid  = [r for r in rows if r["bucket"] == "middle"]
    low  = [r for r in rows if r["bucket"] == "low"]

    picked: List[Dict[str, Any]] = []

    # 예외: High가 충분하면 High 4로
    if len(high) >= need:
        picked = high[:need]
        return {"high": picked, "middle": [], "low": [], "picked": picked}

    # 기본: 1/1/2
    take_high = min(1, len(high))
    picked.extend(high[:take_high])

    take_mid = min(1, len(mid))
    picked.extend(mid[:take_mid])

    take_low = min(2, len(low))
    picked.extend(low[:take_low])

    # 부족분 보충(점수순)
    if len(picked) < need:
        remain = [r for r in rows if r not in picked]
        picked.extend(remain[:(need - len(picked))])

    # 최종 need 컷
    picked = picked[:need]

    # 리포트용 버킷 재구성
    chosen_ids = set((r["doc_id"], r["session_id"]) for r in picked)
    high_fin = [r for r in picked if r["bucket"] == "high"]
    mid_fin  = [r for r in picked if r["bucket"] == "middle"]
    low_fin  = [r for r in picked if r["bucket"] == "low"]

    return {"high": high_fin, "middle": mid_fin, "low": low_fin, "picked": picked}

# -------------------- 프롬프트 빌더 --------------------
def build_chat_prompt(
    db: Session,
    user_id: int,
    turn: int,
    session_id: str
):
    yymmdd = session_id.split('_')[0]

    # 1) 최근 유저 메시지(원문/전처리)
    user_message = db.query(ChatMessage).filter(
        ChatMessage.user_id == user_id,
        ChatMessage.session_id == session_id,
        ChatMessage.turn == turn,
        ChatMessage.role == "user"
    ).first()

    user_query_raw = user_message.message if user_message else ""
    user_query = _preprocess_query(user_query_raw)  # 검색용

    # 2) 하이브리드 검색
    hybrid = HybridMemoryService()
    retrieved = hybrid.hybrid_retrieve(
        user_query=user_query,
        user_id=user_id,
        yymmdd=yymmdd,
        top_k=12,
    )

    # 3) 버킷 규칙으로 최종 4개 선정
    chosen = _select_sessions_by_bucket(retrieved, need=4)
    picked = chosen["picked"]

    # 4) 선정된 세션들의 summary DB 조회
    session_ids = [r["session_id"] for r in picked]
    summaries: Dict[str, str] = {}
    if session_ids:
        rows = db.query(GPTSessionSummary).filter(
            and_(
                GPTSessionSummary.user_id == user_id,
                GPTSessionSummary.session_id.in_(session_ids)
            )
        ).all()
        for row in rows:
            summaries[row.session_id] = row.summary

    # 5) 컨텍스트 블록 구성
    def _fmt_block(tag: str, sess_id: str, text: str) -> str:
        return f"[가능성_{tag}] (session={sess_id}) {text}"

    blocks: List[str] = []
    if chosen["high"]:
        blocks.append(_fmt_block("high", chosen["high"][0]["session_id"], summaries.get(chosen["high"][0]["session_id"], "")))
    else:
        blocks.append("[가능성_high] 없음")

    if chosen["middle"]:
        blocks.append(_fmt_block("middle", chosen["middle"][0]["session_id"], summaries.get(chosen["middle"][0]["session_id"], "")))
    else:
        blocks.append("[가능성_middle] 없음")

    if chosen["low"]:
        for r in chosen["low"][:2]:
            blocks.append(_fmt_block("low", r["session_id"], summaries.get(r["session_id"], "")))
    else:
        blocks.append("[가능성_low] 없음")
        blocks.append("[가능성_low] 없음")

    context_str = "\n".join(blocks)

    # 5.5) 현재 활성 세션의 대화 로그(시간순) 추가
    # - 중복 방지: 현재 turn 이전까지의 메시지만 넣음
    today_chats = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.user_id == user_id,
            ChatMessage.session_id == session_id,
            ChatMessage.turn < turn,         # 현재 턴 중복 방지 (원하면 제거)
        )
        .order_by(
            ChatMessage.turn.asc(),
            case((ChatMessage.role == "user", 0), else_=1),  # user 먼저
            ChatMessage.timestamp.asc(),                     # 타이브레이커
            ChatMessage.id.asc(),                            # 최종 안정화
        )
        .all()
    )

    active_session_header = {
        "role": "system",
        "content": (
            f"[현재 활성 세션 로그]\n"
            f"- session_id={session_id}, yymmdd={yymmdd}\n"
            f"- 아래는 시간순 대화입니다(가장 과거 → 최신)."
        )
    }
    active_session_msgs = [{"role": chat.role, "content": chat.message} for chat in today_chats]

    # 6) 최종 프롬프트 조립
    prompt_messages = [
        {
            "role": "system",
            "content": (
                "너는 사용자의 과거 맥락을 활용해 답하는 보조자야.격식차리지말고 , 편안하게 친구처럼 대화해.\n\n"
                "맥락은 3단계 가능성(high/middle/low)으로 분류되어 제공된다:\n"
                "- 가능성_high: 현재 질문과 매우 강하게 연관된 과거 세션 요약 (신뢰도 높음)\n"
                "- 가능성_middle: 어느 정도 연관성이 있는 세션 요약 (보조적 참고)\n"
                "- 가능성_low: 약한 연관성만 있는 세션 요약 (필요 시만 참고)\n\n"
                "응답 시 high를 가장 우선적으로 활용하고, middle/low는 참고 수준으로 사용해라."
            )
        },
        {"role": "system", "content": f"관련 맥락:\n{context_str}" if context_str else "관련 맥락: (없음)"},
        active_session_header,
        *active_session_msgs,
        {"role": "user", "content": user_query_raw},
    ]

    print(f"✔️ gpt_기억으로 하는prompt 구성 : {prompt_messages}")
    return prompt_messages