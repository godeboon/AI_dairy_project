# 🚀 Matabus Chat API 배포 가이드

## 📋 목차
- [시스템 요구사항](#시스템-요구사항)
- [빠른 시작](#빠른-시작)
- [상세 배포 과정](#상세-배포-과정)
- [환경변수 설정](#환경변수-설정)
- [문제 해결](#문제-해결)

## 🔧 시스템 요구사항

### 필수 요구사항
- **Docker**: 20.10.0 이상
- **Docker Compose**: 2.0.0 이상
- **메모리**: 최소 4GB RAM
- **디스크**: 최소 10GB 여유 공간

### 권장 사양
- **메모리**: 8GB RAM 이상
- **CPU**: 4코어 이상
- **디스크**: SSD 20GB 이상

## ⚡ 빠른 시작

### 1단계: 프로젝트 클론
```bash
git clone https://github.com/your-username/matabus-chat-api.git
cd matabus-chat-api
```

### 2단계: 환경변수 설정
```bash
# 환경변수 파일 복사
cp env.production .env.production

# 실제 API 키 입력
nano .env.production
```

### 3단계: 서비스 시작
```bash
# 실행 권한 부여 (Linux/Mac)
chmod +x *.sh

# 서비스 시작
./start.sh
```

### 4단계: 접속 확인
- **웹 애플리케이션**: http://localhost:8000
- **Chroma 관리**: http://localhost:8001

## 📖 상세 배포 과정

### 개발자 (배포자)

#### 1. Docker Hub 계정 생성
1. [Docker Hub](https://hub.docker.com) 방문
2. 계정 생성 및 로그인
3. 리포지토리 생성: `your-username/matabus-app`

#### 2. 환경변수 설정
```bash
export DOCKER_USERNAME=your-username
```

#### 3. 배포 실행
```bash
# Linux/Mac
./deploy.sh

# Windows
deploy.bat
```

### 사용자 (서비스 실행자)

#### 1. 프로젝트 다운로드
```bash
git clone https://github.com/your-username/matabus-chat-api.git
cd matabus-chat-api
```

#### 2. 환경변수 설정
```bash
# 환경변수 파일 복사
cp env.production .env.production

# 실제 API 키 입력
nano .env.production  # 또는 vim, code 등
```

#### 3. 서비스 시작
```bash
# 실행 권한 부여 (Linux/Mac)
chmod +x *.sh

# 서비스 시작
./start.sh
```

## ⚙️ 환경변수 설정

### 필수 환경변수
```env
# API 키 (실제 값으로 교체 필요)
OPENAI_API_KEY=sk-your-openai-key-here
MIXTRAL_TOKEN=your-mixtral-token-here

# 보안 키 (실제 값으로 교체 필요)
SECRET_KEY=your-super-secret-key-here
```

### 선택적 환경변수
```env
# 데이터베이스
DATABASE_URL=sqlite:///./app.db

# Redis 설정
REDIS_HOST=redis
REDIS_PORT=6379

# Chroma 설정
CHROMA_HOST=chroma
CHROMA_PORT=8000

# 애플리케이션 설정
DEBUG=false
LOG_LEVEL=INFO
```

## 🛠️ 유용한 명령어

### 서비스 관리
```bash
# 서비스 시작
./start.sh

# 서비스 중지
./stop.sh

# 서비스 재시작
docker-compose restart

# 서비스 상태 확인
docker-compose ps
```

### 로그 확인
```bash
# 전체 로그
docker-compose logs

# 실시간 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f web
docker-compose logs -f celery-worker
```

### 데이터 백업
```bash
# 데이터 백업
./backup.sh

# 백업 파일 확인
ls -la backups/
```

## 🔍 문제 해결

### 일반적인 문제들

#### 1. 포트 충돌
```bash
# 포트 사용 확인
netstat -tulpn | grep :8000
netstat -tulpn | grep :8001

# 다른 서비스 중지 후 재시작
./stop.sh
./start.sh
```

#### 2. 메모리 부족
```bash
# 메모리 사용량 확인
docker stats

# 불필요한 컨테이너 정리
docker system prune -a
```

#### 3. 환경변수 오류
```bash
# 환경변수 파일 확인
cat .env.production

# 환경변수 파일 재생성
cp env.production .env.production
```

#### 4. 이미지 빌드 실패
```bash
# Docker 캐시 정리
docker system prune -a

# 이미지 재빌드
docker-compose build --no-cache
```

### 로그 분석
```bash
# 오류 로그 확인
docker-compose logs | grep -i error

# 특정 서비스 상태 확인
docker-compose exec web curl -f http://localhost:8000/health
```

## 📞 지원

문제가 지속되면 다음을 확인하세요:
1. [DOCKER.md](DOCKER.md) - Docker 사용법
2. [Issues](https://github.com/your-username/matabus-chat-api/issues) - 알려진 문제들
3. [Discussions](https://github.com/your-username/matabus-chat-api/discussions) - 커뮤니티 지원

## 🔄 업데이트

### 서비스 업데이트
```bash
# 최신 코드 가져오기
git pull origin main

# 서비스 재시작
./stop.sh
./start.sh
```

### 데이터 마이그레이션
```bash
# 백업 생성
./backup.sh

# 서비스 업데이트
git pull origin main
./stop.sh
./start.sh
```
