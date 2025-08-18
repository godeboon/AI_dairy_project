#  AI 대화 기반 지능형 다이어리 시스템

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.3+-yellow.svg)
![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-blue.svg)
![Redis](https://img.shields.io/badge/Redis-Cache-red.svg)

**AI와의 자연스러운 대화를 통해 자동으로 다이어리를 생성하는 지능형 시스템**

[🚀 프로젝트 소개](#-프로젝트-소개) • [💡 핵심 기능](#-핵심-기능) • [🧠 AI 기술 구현](#-ai-기술-구현) • [🛠️ 기술 스택](#️-기술-스택) • [📊 시스템 아키텍처](#-시스템-아키텍처)

</div>

---

## 1. 프로젝트 소개

**해당프로젝트트**는 사용자와 AI의 자연스러운 대화를 기반으로 하여 자동으로 개인화된 다이어리를 생성하는 혁신적인 시스템입니다. 

### 🎯 핵심 아이디어
- **대화 기반 다이어리**: 사용자가 AI와 대화하는 것만으로도 자동으로 다이어리가 생성됨
- **맥락 인식 대화**: 과거 대화 히스토리를 기억하여 연속성 있는 대화 제공
- **실시간 스트리밍**: AI가 다이어리를 작성하는 과정을 실시간으로 확인 가능


---

## 2. 핵심 기능

### 2-1. AI 대화 기반 다이어리 생성
- **자동 다이어리 생성**: 사용자와의 대화 내용을 분석하여 AI가 자동으로 다이어리 작성
- **실시간 스트리밍**: 다이어리 생성 과정을 실시간으로 스트리밍하여 투명성 제공
- **조건부 생성**: 최소 토큰 수(55개) 이상의 대화가 있어야 다이어리 생성 가능
- **중복 방지**: 하루에 한 번만 AI 다이어리 생성 가능

### 2-2. 하이브리드 메모리 시스템
- **과거 대화 기억**: 사용자의 이전 대화 내용을 정확히 기억하고 참조
- **맥락 인식**: 대화의 맥락을 유지하여 자연스러운 대화 흐름 제공
- **하이브리드 검색**: Sparse(키워드) + Dense(의미) 검색을 결합한 정확한 정보 검색
- **시간 기반 가중치**: 최근 대화일수록 높은 우선순위로 검색

### 2-3. 실시간 통신 시스템
- **WebSocket 연결**: 실시간 양방향 통신으로 즉각적인 응답
- **Redis Pub/Sub**: 실시간 알림 및 이벤트 처리
- **연결 상태 관리**: 안정적인 WebSocket 연결 유지 및 오류 복구
- **다중 채널 구독**: 일기, 격려, 리포트 등 다양한 알림 채널 지원

### 2-4. 학습 분석 및 인사이트
- **세션 분석**: 대화 세션별 상세 분석 및 요약
- **주간 리포트**: 사용자의 대화 패턴과 감정 상태를 주간 단위로 분석
- **격려 시스템**: 사용자의 감정 상태에 따른 맞춤형 격려 메시지 제공
- **개인화 추천**: 오늘의 대화 데이터 기반 맞춤형 콘텐츠(음악) 추천

---

## 3. AI 기술 구현

### 3-1. 하이브리드 검색 엔진
```python
# Weighted RRF (Reciprocal Rank Fusion) 기반 검색
def hybrid_retrieve(self, user_query: str, user_id: int, yymmdd: str):
    # 1. Sparse 검색 (키워드 기반)
    sparse_hits = self._search_sparse(q, user_id=user_id)
    
    # 2. Dense 검색 (의미 기반)
    dense_hits = self._search_dense(q, user_id=user_id)
    
    # 3. Weighted RRF로 결합
    fused = self._weighted_rrf_aggregate(sparse_hits, dense_hits)
    
    # 4. 시간 감쇠 및 보너스 적용
    self._apply_time_decay(doc, now)
    self._apply_bonuses(doc)
```

**핵심 특징:**
- **토큰 수 기반 가중치**: 짧은 질문(≤2토큰)은 Sparse 검색 우선, 긴 질문(>20토큰)은 Dense 검색 우선
- **타입별 가중치**: summary, key_sentence, keywords_all, keyword 등 타입별 차등 가중치
- **시간 감쇠**: 3주 후부터 주당 5% 감쇠로 최신 정보 우선
- **버킷 분류**: High(≥3 hits), Middle(2 hits), Low(1 hit)로 관련성 분류

### 3-2. 맥락 인식 대화 시스템
```python
# 대화 히스토리 기반 맥락 유지
def _resolve_ids(self, meta: Dict[str, Any], source: str, text: str):
    # 세션 단위로 대화 그룹핑
    doc_id = f"{user_id}:{session_id}"
    return doc_id, session_id, yymmdd
```

**구현 방식:**
- **세션 기반 그룹핑**: 동일 세션의 대화를 하나의 문서로 묶어 맥락 유지
- **다중 모달리티**: Sparse + Dense 검색으로 키워드와 의미 모두 고려
- **타입 다양성 보너스**: 다양한 타입의 정보가 검색될 때 가중치 증가
- **모달리티 교차 보너스**: Sparse와 Dense 모두에서 검색될 때 가중치 증가

### 3-3. AI 다이어리 생성 엔진
```python
async def generate_diary_stream(self, user_id: int):
    # 1. 오늘 사용자 채팅 데이터 수집
    formatted_chats, total_tokens = self.chat_repository.diary_get_today_user_chat_and_tokens(user_id)
    
    # 2. 프롬프트 생성
    prompt = self.prompt_service.generate_diary_prompt(formatted_chats)
    
    # 3. 스트리밍 GPT 호출
    async for chunk in self.gpt_client.stream_gpt_response(prompt):
        yield chunk  # 실시간 스트리밍
```

**생성 과정:**
- **대화 데이터 수집**: 사용자의 오늘 대화 내용을 토큰 단위로 분석
- **프롬프트 엔지니어링**: 대화 내용을 다이어리 형태로 변환하는 프롬프트 생성
- **스트리밍 생성**: GPT-4를 활용한 실시간 다이어리 생성
- **자동 저장**: 생성 완료 후 자동으로 데이터베이스에 저장

---

## 4. 기술 스택

### Backend Framework
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **SQLAlchemy**: ORM을 통한 데이터베이스 관리
- **Pydantic**: 데이터 검증 및 직렬화

### AI & Machine Learning
- **OpenAI GPT-4**: 고급 자연어 처리 및 다이어리 생성
- **LangChain**: AI 애플리케이션 개발 프레임워크
- **Sentence Transformers**: 텍스트 임베딩 생성
- **ChromaDB**: 벡터 데이터베이스 (Dense 검색)

### Database & Search
- **SQLite**: 개발 환경 데이터베이스
- **FTS5**: SQLite Full-Text Search (Sparse 검색)
- **Redis**: 캐싱 및 실시간 메시지 브로커

### Real-time Communication
- **WebSocket**: 실시간 양방향 통신
- **Redis Pub/Sub**: 실시간 알림 및 이벤트 처리
- **Server-Sent Events**: 실시간 데이터 스트리밍

### Task Queue & Background Jobs
- **Celery**: 비동기 작업 처리
- **RabbitMQ**: 메시지 브로커

---

## 5. 시스템 아키텍처

### 전체 시스템 구조
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   AI Services   │
│   (Web/App)     │◄──►│   Backend       │◄──►│   (GPT-4)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │ WebSocket             │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis         │    │   Database      │    │   Vector DB     │
│   Pub/Sub       │    │   (SQLite/PG)   │    │   (ChromaDB)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │
        │                       │
        ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   FTS5          │    │   Celery        │
│   Sparse Search │    │   Workers       │
└─────────────────┘    └─────────────────┘
```

### 하이브리드 검색 아키텍처
```
사용자 질문
    │
    ▼
┌─────────────────┐
│ 토큰 수 분석    │
│ (≤2, ≤6, ≤20, >20) │
└─────────────────┘
    │
    ▼
┌─────────────────┐    ┌─────────────────┐
│ Sparse Search   │    │ Dense Search    │
│ (FTS5)          │    │ (ChromaDB)      │
│ 키워드 기반     │    │ 의미 기반       │
└─────────────────┘    └─────────────────┘
    │                       │
    └───────────┬───────────┘
                ▼
┌─────────────────────────────┐
│ Weighted RRF Fusion         │
│ - 토큰 수 기반 가중치       │
│ - 타입별 가중치             │
│ - 시간 감쇠                 │
└─────────────────────────────┘
                ▼
┌─────────────────────────────┐
│ 버킷 분류                   │
│ High(≥3), Middle(2), Low(1) │
└─────────────────────────────┘
```

### 프로젝트 구조
```
app/
├── api/routers/              # API 엔드포인트
│   ├── auth_router.py        # 인증 관련 API
│   ├── chat_router.py        # 채팅 메시지 API
│   ├── study_router.py       # 다이어리 생성 API
│   └── websocket_router.py   # 실시간 통신 API
├── services/                 # 비즈니스 로직
│   ├── hybrid_memory_service.py  # 하이브리드 검색 엔진
│   ├── diary_service.py      # 다이어리 생성 서비스
│   ├── websocket_service.py  # 실시간 통신 서비스
│   ├── embedding_service.py  # 임베딩 서비스
│   └── vector_db_service.py  # 벡터 데이터베이스
├── models/                   # 데이터 모델
│   ├── db/                  # 데이터베이스 모델
│   └── schemas/             # Pydantic 스키마
├── tasks/                   # 백그라운드 작업
├── config/                  # 설정 관리
└── utils/                   # 유틸리티 함수
```

---

## 6. 핵심 성과

### 기술적 성과
- **하이브리드 검색 정확도**: Sparse + Dense 검색 결합으로 신뢰 높은 검색 매칭률 확보
- **맥락 인식**: 과거 대화 히스토리 기반 맥락유지 가능


### 사용자 경험 성과
- **다이어리(일기) 생성 자동화**: 오늘의 대화 내용을 바탕으로 자동 다이어리 생성
- **실시간 피드백**: 다이어리 생성 과정의 실시간 스트리밍으로 투명성 제공
- **사용자 만족도**: AI 대화 기반 다이어리 뿐만 아니라 유저가 직접 작성 가능한 일기 두가지 방식으로 제공



---

##  7.시작하기

### 1. 환경 설정
```bash
# 저장소 클론
git clone https://github.com/your-username/matabus.git
cd matabus

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
# 환경변수 파일 복사
cp env.example .env

# .env 파일 편집
# - OPENAI_API_KEY: OpenAI API 키
# - SECRET_KEY: JWT 시크릿 키
# - REDIS_HOST: Redis 서버 주소
# - DATABASE_URL: 데이터베이스 연결 문자열
```

### 3. 데이터베이스 설정
```bash
# SQLite 데이터베이스 자동 생성 (기본값)
# 또는 PostgreSQL 설정
```

### 4. 서버 실행
```bash
# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery 워커 실행 (별도 터미널)
celery -A app.services.celery_app worker --loglevel=info
```




## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

---

## 📞 연락처

- **이메일**: kjkj750@naver.com
- **GitHub**: [Your GitHub Profile]([https://github.com/your-username](https://github.com/godeboon/AI_dairy_project))

---

<div align="center">


</div> 
