#!/bin/bash

# Matabus Chat API 데이터 백업 스크립트
echo "💾 Matabus Chat API 데이터 백업을 시작합니다..."

# 백업 디렉토리 생성
BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"

mkdir -p "$BACKUP_PATH"

echo "📁 백업 디렉토리: $BACKUP_PATH"

# Docker Compose 설치 확인
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되지 않았습니다."
    exit 1
fi

# 서비스가 실행 중인지 확인
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  서비스가 실행 중이 아닙니다. 백업을 계속하시겠습니까? (y/N)"
    read -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 백업이 취소되었습니다."
        exit 1
    fi
fi

# Redis 데이터 백업
echo "📦 Redis 데이터 백업 중..."
docker-compose exec -T redis redis-cli BGSAVE
sleep 2
docker cp $(docker-compose ps -q redis):/data/dump.rdb "$BACKUP_PATH/redis_dump.rdb"

if [ $? -eq 0 ]; then
    echo "✅ Redis 데이터 백업 완료"
else
    echo "❌ Redis 데이터 백업 실패"
fi

# Chroma 데이터 백업
echo "📦 Chroma 데이터 백업 중..."
docker cp $(docker-compose ps -q chroma):/chroma/chroma "$BACKUP_PATH/chroma_data/"

if [ $? -eq 0 ]; then
    echo "✅ Chroma 데이터 백업 완료"
else
    echo "❌ Chroma 데이터 백업 실패"
fi

# 애플리케이션 데이터 백업
echo "📦 애플리케이션 데이터 백업 중..."
docker cp $(docker-compose ps -q web):/app/data "$BACKUP_PATH/app_data/"

if [ $? -eq 0 ]; then
    echo "✅ 애플리케이션 데이터 백업 완료"
else
    echo "❌ 애플리케이션 데이터 백업 실패"
fi

# 환경변수 파일 백업
echo "📦 환경변수 파일 백업 중..."
if [ -f ".env.production" ]; then
    cp .env.production "$BACKUP_PATH/"
    echo "✅ 환경변수 파일 백업 완료"
else
    echo "⚠️  .env.production 파일이 없습니다."
fi

# 백업 정보 파일 생성
echo "📝 백업 정보 생성 중..."
cat > "$BACKUP_PATH/backup_info.txt" << EOF
백업 일시: $(date)
백업 버전: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
Docker Compose 버전: $(docker-compose --version)
백업 내용:
- Redis 데이터 (dump.rdb)
- Chroma 벡터 데이터베이스
- 애플리케이션 데이터
- 환경변수 파일

복원 방법:
1. ./stop.sh (서비스 중지)
2. docker volume rm matabus_redis_data matabus_chroma_data matabus_app_data
3. ./start.sh (서비스 시작)
4. docker cp backup_$TIMESTAMP/redis_dump.rdb \$(docker-compose ps -q redis):/data/
5. docker cp backup_$TIMESTAMP/chroma_data/ \$(docker-compose ps -q chroma):/chroma/
6. docker cp backup_$TIMESTAMP/app_data/ \$(docker-compose ps -q web):/app/
7. docker-compose restart
EOF

# 백업 압축
echo "🗜️  백업 압축 중..."
cd "$BACKUP_DIR"
tar -czf "backup_$TIMESTAMP.tar.gz" "backup_$TIMESTAMP"
rm -rf "backup_$TIMESTAMP"
cd ..

# 백업 크기 확인
BACKUP_SIZE=$(du -h "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" | cut -f1)

echo ""
echo "✅ 백업이 성공적으로 완료되었습니다!"
echo "📁 백업 파일: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz"
echo "📊 백업 크기: $BACKUP_SIZE"
echo ""
echo "📋 백업 파일 목록:"
ls -la "$BACKUP_DIR/"

echo ""
echo "💡 백업 파일을 안전한 곳에 보관하세요!"
echo "   예: 외부 저장소, 클라우드 스토리지 등"
