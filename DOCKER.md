# 🐳 Docker 사용법 가이드

## 📋 목차
- [Docker 설치](#docker-설치)
- [기본 개념](#기본-개념)
- [프로젝트 구조](#프로젝트-구조)
- [서비스 구성](#서비스-구성)
- [명령어 가이드](#명령어-가이드)
- [문제 해결](#문제-해결)

## 🔧 Docker 설치

### Windows
1. [Docker Desktop for Windows](https://docs.docker.com/desktop/windows/install/) 다운로드
2. 설치 후 재부팅
3. Docker Desktop 실행

### macOS
1. [Docker Desktop for Mac](https://docs.docker.com/desktop/mac/install/) 다운로드
2. 설치 후 Docker Desktop 실행

### Linux (Ubuntu/Debian)
```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
```

## 🧠 기본 개념

### Docker 컨테이너
- **컨테이너**: 애플리케이션과 의존성을 패키지화한 실행 환경
- **이미지**: 컨테이너를 생성하는 템플릿
- **볼륨**: 데이터 영속성을 위한 저장 공간

### Docker Compose
- **서비스**: 여러 컨테이너를 하나의 애플리케이션으로 관리
- **네트워크**: 컨테이너 간 통신
- **볼륨**: 데이터 공유 및 영속성

## 📁 프로젝트 구조

```
matabus-chat-api/
├── Dockerfile              # 애플리케이션 이미지 빌드
├── docker-compose.yml      # 서비스 오케스트레이션
├── .dockerignore           # 빌드 시 제외할 파일들
├── env.production          # 환경변수 템플릿
├── deploy.sh              # 배포 스크립트
├── start.sh               # 서비스 시작
├── stop.sh                # 서비스 중지
├── backup.sh              # 데이터 백업
└── app/                   # 애플리케이션 코드
```

## 🏗️ 서비스 구성

### 1. Redis 서버
```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```
- **용도**: Celery 브로커, 캐시
- **포트**: 6379
- **데이터**: 영속성 보장

### 2. Chroma 벡터 데이터베이스
```yaml
chroma:
  image: chromadb/chroma:latest
  ports:
    - "8001:8000"
  volumes:
    - chroma_data:/chroma/chroma
```
- **용도**: 벡터 데이터베이스
- **포트**: 8001 (외부), 8000 (내부)
- **데이터**: 벡터 임베딩 저장

### 3. FastAPI 웹 애플리케이션
```yaml
web:
  build: .
  ports:
    - "8000:8000"
  depends_on:
    - redis
    - chroma
```
- **용도**: 웹 API 서버
- **포트**: 8000
- **의존성**: Redis, Chroma

### 4. Celery Worker
```yaml
celery-worker:
  build: .
  command: python -m celery -A app.services.celery_app:celery worker --loglevel=info --pool=solo
```
- **용도**: 백그라운드 작업 처리
- **의존성**: Redis

### 5. Celery Beat
```yaml
celery-beat:
  build: .
  command: python -m celery -A app.services.celery_app:celery beat --loglevel=info
```
- **용도**: 스케줄러
- **의존성**: Redis

## 🎯 명령어 가이드

### 기본 명령어

#### 서비스 시작
```bash
# 전체 서비스 시작
docker-compose up -d

# 또는 스크립트 사용
./start.sh
```

#### 서비스 중지
```bash
# 전체 서비스 중지
docker-compose down

# 또는 스크립트 사용
./stop.sh
```

#### 서비스 상태 확인
```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 리소스 사용량 확인
docker stats
```

### 로그 관련

#### 로그 확인
```bash
# 전체 로그
docker-compose logs

# 실시간 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f web
docker-compose logs -f celery-worker
```

#### 로그 필터링
```bash
# 오류 로그만 확인
docker-compose logs | grep -i error

# 특정 시간대 로그
docker-compose logs --since="2024-01-01T00:00:00"
```

### 컨테이너 관리

#### 컨테이너 접속
```bash
# 웹 컨테이너 접속
docker-compose exec web bash

# Redis 컨테이너 접속
docker-compose exec redis redis-cli
```

#### 컨테이너 재시작
```bash
# 특정 서비스 재시작
docker-compose restart web

# 전체 서비스 재시작
docker-compose restart
```

### 이미지 관리

#### 이미지 빌드
```bash
# 이미지 빌드
docker-compose build

# 캐시 없이 빌드
docker-compose build --no-cache

# 특정 서비스만 빌드
docker-compose build web
```

#### 이미지 정리
```bash
# 사용하지 않는 이미지 삭제
docker image prune

# 모든 이미지 삭제
docker image prune -a
```

### 볼륨 관리

#### 볼륨 확인
```bash
# 볼륨 목록
docker volume ls

# 볼륨 상세 정보
docker volume inspect matabus_redis_data
```

#### 볼륨 백업
```bash
# 백업 스크립트 사용
./backup.sh

# 수동 백업
docker run --rm -v matabus_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz -C /data .
```

## 🔍 문제 해결

### 일반적인 문제들

#### 1. 포트 충돌
```bash
# 포트 사용 확인
netstat -tulpn | grep :8000
lsof -i :8000

# 해결 방법
./stop.sh
# 다른 서비스 중지 후
./start.sh
```

#### 2. 메모리 부족
```bash
# 메모리 사용량 확인
docker stats

# 해결 방법
docker system prune -a
```

#### 3. 이미지 빌드 실패
```bash
# Docker 캐시 정리
docker system prune -a

# 이미지 재빌드
docker-compose build --no-cache
```

#### 4. 컨테이너 시작 실패
```bash
# 로그 확인
docker-compose logs web

# 컨테이너 상태 확인
docker-compose ps
```

### 네트워크 문제

#### 컨테이너 간 통신 확인
```bash
# 네트워크 확인
docker network ls
docker network inspect matabus_network

# 컨테이너 간 연결 테스트
docker-compose exec web ping chroma
docker-compose exec web ping redis
```

### 데이터 문제

#### 데이터 손실 방지
```bash
# 정기적 백업
./backup.sh

# 볼륨 확인
docker volume ls
```

#### 데이터 복구
```bash
# 백업에서 복구
tar -xzf backups/backup_20240101_120000.tar.gz
docker cp backup_20240101_120000/redis_dump.rdb $(docker-compose ps -q redis):/data/
```

## 📊 모니터링

### 헬스체크
```bash
# 서비스 상태 확인
docker-compose ps

# 헬스체크 로그
docker-compose logs | grep health
```

### 성능 모니터링
```bash
# 리소스 사용량
docker stats

# 컨테이너 상세 정보
docker inspect $(docker-compose ps -q web)
```

## 🔧 고급 설정

### 환경변수 오버라이드
```bash
# 특정 환경변수로 실행
REDIS_HOST=localhost docker-compose up -d
```

### 개발 모드
```bash
# 개발용 docker-compose 파일 사용
docker-compose -f docker-compose.dev.yml up -d
```

### 프로덕션 모드
```bash
# 프로덕션용 설정
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 추가 자료

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 공식 문서](https://docs.docker.com/compose/)
- [Redis 공식 문서](https://redis.io/documentation)
- [Chroma 공식 문서](https://docs.trychroma.com/)
