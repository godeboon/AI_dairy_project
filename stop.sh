#!/bin/bash

# Matabus Chat API 서비스 중지 스크립트
echo "🛑 Matabus Chat API 서비스를 중지합니다..."

# Docker Compose 설치 확인
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되지 않았습니다."
    exit 1
fi

# 서비스 상태 확인
echo "📊 현재 서비스 상태:"
docker-compose ps

# 서비스 중지
echo "🛑 서비스 중지 중..."
docker-compose down

if [ $? -ne 0 ]; then
    echo "❌ 서비스 중지 실패"
    exit 1
fi

# 컨테이너 정리 (선택사항)
read -p "🗑️  사용하지 않는 컨테이너와 이미지를 정리하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 사용하지 않는 컨테이너 정리 중..."
    docker container prune -f
    
    echo "🧹 사용하지 않는 이미지 정리 중..."
    docker image prune -f
    
    echo "🧹 사용하지 않는 볼륨 정리 중..."
    docker volume prune -f
fi

echo ""
echo "✅ 서비스가 성공적으로 중지되었습니다!"
echo ""
echo "📋 유용한 명령어:"
echo "   - 서비스 시작: ./start.sh"
echo "   - 로그 확인: docker-compose logs"
echo "   - 완전 정리: docker-compose down -v --rmi all"
