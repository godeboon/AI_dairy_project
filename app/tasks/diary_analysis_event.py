from celery import shared_task
from sqlalchemy.orm import sessionmaker
from app.core.connection import engine
from app.repositories.weekly_analysis_repository import WeeklyAnalysisRepository
from app.services.weekly_analysis_service import WeeklyAnalysisService
from app.config.settings import settings
import redis
import json

SessionLocal = sessionmaker(bind=engine)
redis_client = redis.Redis(
    host=settings.redis_host, 
    port=settings.redis_port, 
    db=settings.redis_db
)


# diary_anaylsis report 7번 업뎃되면 weekly 실행하기 위한 이벤트 리스너 


@shared_task
def check_weekly_analysis_after_diary_save(user_id: int):
    """DiaryAnalysisReport 저장 후 주간 분석 체크"""
    print(f"🔄 주간 분석 체크 시작: user_id={user_id}")
    
    db = SessionLocal()
    try:
        weekly_repo = WeeklyAnalysisRepository(db)
        
        # 1. 사용되지 않은 일일 분석 리포트 조회 (날짜순 정렬)
        unused_reports = weekly_repo.get_unused_weekly_reports(user_id, 7)
        
        # 2. 7일치가 모였는지 확인
        if len(unused_reports) >= 7:
            # 3. 주간 분석 실행
            service = WeeklyAnalysisService(db)
            result = service.analyze_weekly_data(user_id)
            
            if result:
                # 4. WebSocket 알림 발행 (일기 생성과 동일한 패턴)
                message = {
                    "type": "seven_day_report",
                    "target": "study-section",
                    "message": "7일 감정 레포트가 완성되었습니다!",
                    "user_id": user_id
                }
                redis_client.publish(f"user_{user_id}_report", json.dumps(message))
                
                print(f"✅ 주간 분석 완료 및 알림 발행: user_id={user_id}")
            else:
                print(f"❌ 주간 분석 실패: user_id={user_id}")
        else:
            print(f"⏳ 아직 7일치 모이지 않음: user_id={user_id}, days={len(unused_reports)}")
            
    except Exception as e:
        print(f"❌ 주간 분석 체크 실패: {str(e)}")
    finally:
        db.close() 