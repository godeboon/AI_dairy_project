#  AI 대화 기반 지능형 다이어리 시스템 (MVP)
LangChain 기반 AI 대화형 다이어리(MVP): Dense+Sparse(RRF) 하이브리드 검색, WebSocket 알림으로 프론트 UI 변화 


<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.3%2B-yellow.svg)
![ChromaDB](https://img.shields.io/badge/Chroma-VectorDB-informational.svg)
![SQLite](https://img.shields.io/badge/SQLite-FTS5%2FBM25-lightgrey.svg)
![WebSocket](https://img.shields.io/badge/WebSocket-Realtime-blue.svg)
![Redis](https://img.shields.io/badge/Redis-Pub%2FSub-red.svg)

**세션이 종료된 이후에도 과거 대화 맥락을 회수해 안정적으로 반영하는 AI 대화형 다이어리 시스템**  
(MVP, **로컬 실행** 지원)

</div>

---

## 🚀 소개

Matabus는 사용자와의 자연스러운 대화를 구조화하여 **자동으로 일기(다이어리)를 생성**합니다.  
핵심은 **하이브리드 Retrieval(Dense + Sparse)** 과 **프롬프트 오케스트레이션**이며, **Weighted-RRF, 시간 감쇠, 버킷 주입**을 통해 **정확하고 일관된 응답**을 지향합니다.

> “일주일 차트” 서브탭은 **준비 중**입니다(감정/키워드 추세 시각화 / 7일간의 변화 추적 ).

---

## 💡 핵심 기능

- **대화 기반 자동 다이어리**
  - 오늘 대화가 **최소 토큰 수(예: 55)** 를 넘고, **해당 날짜에 아직 생성 이력이 없을 때** 일기 자동 생성
  - 실시간 스트리밍으로 작성 과정을 UI에서 확인
- **하이브리드 메모리 & 검색**
  - 세션 종료 시 `summary / key_sentence / keywords_all / keyword` 문서를 생성·임베딩
  - **Dense(Chroma, cosine) + Sparse(SQLite FTS5/BM25)** 동시 조회 → **Weighted-RRF** 융합
  - (type, modality) **고유조합 1회 집계**로 중복 억제, **21일 그레이스 이후 주당 5% 감쇠(하한 0.6)**
  - 증거 강도(n_hits) 기반 **high / middle / low** 버킷 주입
- **실시간 알림(WebSocket)**
  - 서버-클라이언트 **양방향 WebSocket**으로 알림 수신
  - **일기 생성 조건 충족** 시 `diary_ready` 또는 `diary_started` 등 이벤트 발행
  - **오늘의 응원 메시지**가 발송 가능하면 `encourage` 이벤트로 즉시 푸시
  - Redis Pub/Sub을 사용한 안정적 브로드캐스트

---

## 🧠 AI/검색 구현 요약

- **검색**: Sparse(FTS5/BM25) + Dense(Chroma/cosine) **병렬 조회**
- **융합**: `Weighted-RRF`로 통합 스코어 계산, *(type, modality)* 고유조합 1회 집계
- **가중치**: 질의 토큰 길이에 따라 Sparse/Dense 및 Type 가중치 **동적 조정**
- **보정**: 타입 다양성 보너스(≤+0.15), 교차 모달리티 보너스(+0.07)
- **최신성**: 21일 이후 **주당 5% 감쇠**, 하한 0.6
- **선정/주입**: n_hits 기준 **high(≥3) → middle(=2) → low(=1)** 순서로 프롬프트에 제한 수량만 주입

**프롬프트 오케스트레이션(문장형 설명)**  
프롬프트는 **시스템 지침**을 먼저 제시하고, **신뢰도가 높은 컨텍스트부터 낮은 컨텍스트 순서로** 필요한 개수만 넣은 뒤 **최신 대화**를 덧붙입니다. 전체 길이는 **토큰 예산** 내에서 관리하며, 초과 시 **절단 규칙**을 적용해 안정성을 유지합니다.

---

## 🔔 WebSocket 알림 규격

- **엔드포인트 예시**
  - `GET /ws/notify?user_id={id}` (쿼리 또는 헤더 토큰으로 인증)
- **이벤트 타입**
  - `diary_ready` : 오늘 대화 토큰이 기준치 이상 & 당일 미생성 → 생성 가능 알림
  - `diary_started` : 스트리밍 생성 시작
  - `diary_chunk` : 생성 중간 청크(옵션, SSE 혼용 가능)
  - `diary_finished` : 생성 완료
  - `encourage` : 오늘의 응원 메시지 발송 가능/발송됨
  - `error` : 오류/권한 문제 등
- **페이로드 예시**
  ```json
  { "type": "diary_ready", "date": "2025-08-17", "min_tokens": 55, "current_tokens": 71 }
  { "type": "encourage", "message": "오늘도 고생했어요. 잠깐 스트레칭 어때요?" }
