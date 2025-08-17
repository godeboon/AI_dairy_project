# Matabus - AI 대화 기반 지능형 다이어리 시스템

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.3+-yellow.svg)
![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-blue.svg)
![Redis](https://img.shields.io/badge/Redis-Cache-red.svg)

**AI와의 자연스러운 대화를 통해 자동으로 다이어리를 생성하는 지능형 시스템**

[프로젝트 소개](#프로젝트-소개) • [핵심 기능](#핵심-기능) • [AI 기술 구현](#ai-기술-구현) • [기술 스택](#기술-스택) • [시스템 아키텍처](#시스템-아키텍처)

</div>

---

## 프로젝트 소개

이 프로젝트는 사용자와 AI의 자연스러운 대화를 기반으로 하여 자동으로 개인화된 다이어리를 생성하는 시스템입니다. 

### 핵심 아이디어
- 대화 기반 다이어리: 사용자가 AI와 대화한 내용을 바탕으로 자동 생성
- 맥락 인식 대화: 과거 대화 히스토리를 기억하여 연속성 있는 대화 제공
- 실시간 스트리밍: AI가 다이어리를 작성하는 과정을 실시간으로 확인 가능

---

## 핵심 기능

### AI 대화 기반 다이어리 생성
- 자동 다이어리 생성: 사용자와의 대화 내용을 분석하여 AI가 자동으로 다이어리 작성
- 실시간 스트리밍: 다이어리 생성 과정을 실시간으로 확인 가능
- 조건부 생성: 최소 토큰 수(55개) 이상의 대화가 있어야 생성
- 중복 방지: 하루에 한 번만 생성 가능

### 하이브리드 메모리 시스템
- 과거 대화 기억: 사용자의 이전 대화 내용을 참조
- 맥락 인식: 대화 맥락을 유지하여 자연스러운 흐름 제공
- 하이브리드 검색: Sparse(키워드) + Dense(의미) 검색 결합
- 시간 기반 가중치: 최근 대화일수록 높은 우선순위 반영

### 실시간 통신 시스템
- WebSocket 연결: 실시간 양방향 통신
- Redis Pub/Sub: 실시간 알림 및 이벤트 처리
- 연결 상태 관리 및 오류 복구
- 다중 채널 구독: 일기, 격려, 리포트 등 다양한 알림 지원

### 학습 분석 및 인사이트
- 세션 분석 및 요약
- 주간 리포트 제공
- 감정 상태 기반 맞춤형 격려 메시지
- 개인화된 콘텐츠 추천

---

## AI 기술 구현

### 하이브리드 검색 엔진
```python
# Weighted RRF (Reciprocal Rank Fusion) 기반 검색
def hybrid_retrieve(self, user_query: str, user_id: int, yymmdd: str):
    sparse_hits = self._search_sparse(q, user_id=user_id)
    dense_hits = self._search_dense(q, user_id=user_id)
    fused = self._weighted_rrf_aggregate(sparse_hits, dense_hits)
    self._apply_time_decay(doc, now)
    self._apply_bonuses(doc)
