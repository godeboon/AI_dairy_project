from celery import shared_task
from sqlalchemy.orm import sessionmaker
from app.core.connection import engine
from app.repositories.similar_pattern_repository import SimilarPatternRepository
from app.services.report_service import ReportService
from app.config.settings import settings
import redis
import json

SessionLocal = sessionmaker(bind=engine)
redis_client = redis.Redis(
    host=settings.redis_host, 
    port=settings.redis_port, 
    db=settings.redis_db
)


# similar_pattern 저장 후 analysis_ids가 3개 이상인지 확인하는 이벤트 리스너


@shared_task
def check_similar_pattern_analysis_ready(user_id: int):
    """SimilarPattern 저장 후 분석 준비 상태 체크"""
    print(f"🔄 유사 패턴 분석 준비 상태 체크 시작: user_id={user_id}")
    
    db = SessionLocal()
    try:
        similar_pattern_repo = SimilarPatternRepository(db)
        
        # 1. user_id로 SimilarPattern 조회 (마킹되지 않은 것만)
        similar_pattern = similar_pattern_repo.get_by_user_id_and_not_used(user_id)
        
        if not similar_pattern:
            print(f"❌ 분석 가능한 유사 패턴 데이터를 찾을 수 없음: user_id={user_id}")
            return
        
        # 2. analysis_ids 리스트가 3개 이상인지 확인
        analysis_ids = similar_pattern.analysis_ids
        if len(analysis_ids) >= 3:
            print(f"✅ 분석 준비 완료: user_id={user_id}, analysis_ids 개수: {len(analysis_ids)}")
            
            # 3. 리포트 서비스 실행
            report_service = ReportService(db)
            result = report_service.generate_comprehensive_report(user_id, similar_pattern.id)
            
            if result:
                # 4. 성격 분석에 사용된 것으로 마킹
                similar_pattern.is_used_in_personality_analysis = True
                similar_pattern_repo.db.commit()
                print(f"✅ 유사 패턴 마킹 완료: similar_pattern_id={similar_pattern.id}")
                
                # 5. WebSocket 알림 발행
                print(f"🔍 result 타입 확인: {type(result)}, 내용: {result}")
                
                # result가 딕셔너리인지 확인하고 안전하게 접근
                if isinstance(result, dict) and "personality_report_id" in result:
                    report_id = result["personality_report_id"]
                    print(f"🔍 report_id 값 확인: {report_id} (타입: {type(report_id)})")
                    
                    message = {
                        "type": "report",
                        "message": "최종리포트 완성!",
                        "user_id": user_id,
                        "report_id": report_id
                    }
                    print(f"🔍 전송할 message 내용: {message}")
                    redis_client.publish(f"user_{user_id}_report", json.dumps(message))
                    print(f"✅ 유사 패턴 종합 분석 완료 및 알림 발행: user_id={user_id}, report_id={report_id}")
                else:
                    print(f"❌ result에 personality_report_id가 없음: {result}")
                    if isinstance(result, dict):
                        print(f"🔍 result의 키들: {list(result.keys())}")
            else:
                print(f"❌ 유사 패턴 종합 분석 실패: user_id={user_id}")
        else:
            print(f"⏳ 아직 분석 준비되지 않음: user_id={user_id}, analysis_ids 개수: {len(analysis_ids)}")
            
    except Exception as e:
        print(f"❌ 유사 패턴 분석 준비 상태 체크 실패: {str(e)}")
    finally:
        db.close()
