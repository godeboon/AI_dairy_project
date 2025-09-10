#!/bin/bash

# Matabus Chat API 서비스 시작 스크립트
echo "🚀 Matabus Chat API 서비스를 시작합니다..."

# 환경변수 파일 확인
if [ ! -f ".env.production" ]; then
    echo "⚠️  .env.production 파일이 없습니다."
    echo "📋 env.production을 복사하여 .env.production을 생성하세요:"
    echo "   cp env.production .env.production"
    echo "   그리고 실제 API 키를 입력하세요."
    exit 1
fi

# Docker 및 Docker Compose 설치 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다."
    echo "   https://docs.docker.com/get-docker/ 에서 설치하세요."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되지 않았습니다."
    echo "   https://docs.docker.com/compose/install/ 에서 설치하세요."
    exit 1
fi

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker-compose down

# 이미지 빌드
echo "🔨 이미지 빌드 중..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ 이미지 빌드 실패"
    exit 1
fi

# 서비스 시작
echo "🚀 서비스 시작 중..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ 서비스 시작 실패"
    exit 1
fi

# 서비스 상태 확인
echo "⏳ 서비스 시작 대기 중..."
sleep 10

echo "📊 서비스 상태 확인:"
docker-compose ps

echo ""
echo "✅ 서비스가 성공적으로 시작되었습니다!"
echo ""
echo "🌐 접속 URL:"
echo "   - 웹 애플리케이션: http://localhost:8000"
echo "   - Chroma 관리: http://localhost:8001"
echo ""
echo "📋 유용한 명령어:"
echo "   - 로그 확인: docker-compose logs -f"
echo "   - 서비스 중지: ./stop.sh"
echo "   - 서비스 재시작: docker-compose restart"
