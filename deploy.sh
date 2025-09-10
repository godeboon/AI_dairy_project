#!/bin/bash

# Matabus Chat API 배포 스크립트
echo "🚀 Matabus Chat API 배포를 시작합니다..."

# Docker Hub 사용자명 확인
if [ -z "$DOCKER_USERNAME" ]; then
    echo "❌ DOCKER_USERNAME 환경변수가 설정되지 않았습니다."
    echo "export DOCKER_USERNAME=your-username 명령어로 설정하세요."
    exit 1
fi

# 이미지 태그 설정
IMAGE_TAG=${1:-latest}
IMAGE_NAME="$DOCKER_USERNAME/yoni_chat_innernote_app:$IMAGE_TAG"

echo "📦 이미지 빌드 중: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" .

if [ $? -ne 0 ]; then
    echo "❌ 이미지 빌드 실패"
    exit 1
fi

echo "🔐 Docker Hub에 로그인하세요..."
docker login

if [ $? -ne 0 ]; then
    echo "❌ Docker Hub 로그인 실패"
    exit 1
fi

echo "📤 이미지 푸시 중: $IMAGE_NAME"
docker push "$IMAGE_NAME"

if [ $? -ne 0 ]; then
    echo "❌ 이미지 푸시 실패"
    exit 1
fi

echo "✅ 배포 완료!"
echo ""
echo "📋 다른 서버에서 실행하는 방법:"
echo "1. git clone your-repo-url"
echo "2. cd your-project"
echo "3. cp env.production .env.production"
echo "4. .env.production 파일에 실제 API 키 입력"
echo "5. docker-compose up -d"
echo ""
echo "🌐 접속 URL: http://localhost:8000"
