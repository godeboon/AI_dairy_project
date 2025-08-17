# tasks.py
import app.models
from celery import Celery
from celery.utils.log import get_task_logger
# from app.services.mixtral_service import SummarizationService
from app.repositories.today_chat_message_repository import TodayChatMessageRepository
from app.core.connection import get_db
from app.models.db.user_model import User
from app.models.db.study_model import DiaryAnalysisReport, EncouragementReport
from app.services.diary_analysis_service import DiaryAnalysisService
from app.services.encourage_diary_service import EncourageDiaryService
from app.config.settings import settings
import redis
import json
from dotenv import load_dotenv
from datetime import datetime, date
from celery.schedules import crontab
from sqlalchemy import func
load_dotenv()

# 🔥 모델 로딩 순서 보장 - 외래키 의존성을 위해 순서 중요!
from app.models.db.session_log import SessionLog  # 1. 먼저 로드
from app.models.db.session_summary import SessionSummary, GPTSessionSummary  # 2. 그 다음 로드


# Redis 클라이언트 설정
print(f"🔗 Celery Redis 연결 시도: {settings.redis_host}:{settings.redis_port}")
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db
)

# 1) 브로커 URL은 이미 환경변수에서 읽어옵니다.
celery = Celery("matabus")

@celery.task
def test_task():
    print("테스트 성공")

logger = get_task_logger(__name__)

# 2) app.task 으로 데코레이트
# @celery.task(bind=True, autoretry_for=(Exception,), max_retries=5, retry_backoff=True)
# def summarize_task(self, user_id: int, session_id: str):
#     logger.info(f"▶ summarize_task 시작: user_id={user_id}, session_id={session_id}")
#     try:
#         service = SummarizationService()
#         service.summarize(user_id, session_id)
#         logger.info(f"✅ summarize_task 완료: user_id={user_id}, session_id={session_id}")
#     except Exception as exc:
#         logger.exception(f"❌ summarize_task 실패, 재시도 준비 중: user_id={user_id}, session_id={session_id}")
#         raise self.retry(exc=exc)

@celery.task(bind=True, autoretry_for=(Exception,), max_retries=5, retry_backoff=True)
def session_summarize_task(self, user_id: int, session_id: str):
    logger.info(f"▶ session_summarize_task 시작: user_id={user_id}, session_id={session_id}")
    try:
        # 🔥 모델 로딩 순서 보장 - 외래키 의존성을 위해
        from app.models.db.session_log import SessionLog
        from app.models.db.session_summary import GPTSessionSummary
        
        from app.services.gpt_session_summary_service import GPTSessionSummaryService
        service = GPTSessionSummaryService()
        service.create_session_summary(user_id, session_id)
        logger.info(f"✅ session_summarize_task 완료: user_id={user_id}, session_id={session_id}")
    except Exception as exc:
        logger.exception(f"❌ session_summarize_task 실패, 재시도 준비 중: user_id={user_id}, session_id={session_id}")
        raise self.retry(exc=exc)




        

# 3) 일기 생성 조건 체크 Task
@celery.task
def check_diary_conditions_periodic():
    """일기 생성 조건 확인 (5분마다 실행)"""
    logger.info("▶ 일기 생성 조건 체크 시작")
    try:
        db = next(get_db())
        # 모든 활성 유저 조회
        users = db.query(User).all()

        for user in users:
            try:
                # Repository를 사용하여 조건 체크
                chat_repo = TodayChatMessageRepository()

                # 1. 오늘 사용자 채팅 토큰수 확인
                formatted_chats, total_tokens = chat_repo.diary_get_today_user_chat_and_tokens(user.id)

                # 2. 오늘 AI 생성 여부 확인 (source_type='ai')
                today_ai_diary = chat_repo.check_today_diary_by_source(user.id, 'ai')

            
                # AI 생성 조건 체크
                # 1. 오늘 사용자 채팅 토큰이 55개 이상
                # 2. 아직 오늘 AI로 일기를 생성하지 않았는지 확인
                if total_tokens >= 55 and not today_ai_diary:
                    # Redis에 알림 발행
                    message = {
                        "type": "diary_available",
                        "user_id": user.id,
                        "message": "오늘의 일기를 생성할 수 있습니다!"
                      
                    }
                    
                    channel = f"user_{user.id}_diary"
                    message_json = json.dumps(message)
                    
                    print(f"📤 Redis 발행 시도: channel={channel}, message={message_json}")
                    
                    try:
                        result = redis_client.publish(channel, message_json)
                        print(f"✅ Redis 발행 성공: channel={channel}, result={result} (구독자 수)")
                        logger.info(f"✅ 일기 생성 알림 발행: user_id={user.id}, 토큰수={total_tokens}")
                    except Exception as e:
                        print(f"❌ Redis 발행 실패: {e}")
                        logger.error(f"❌ Redis 발행 실패: user_id={user.id}, error={e}")
                        
                else:
                    if today_ai_diary:
                        logger.info(f"ℹ️ 이미 오늘 AI 일기 생성됨: user_id={user.id}")
                    else:
                        logger.info(f"ℹ️ 토큰수 부족: user_id={user.id}, 토큰수={total_tokens}")

            except Exception as e:
                logger.error(f"❌ 유저 {user.id} 일기 조건 체크 실패: {e}")

    except Exception as e:
        logger.error(f"❌ 일기 조건 체크 실패: {e}")
    finally:
        db.close()
# def check_diary_conditions_periodic():
#     """일기 생성 조건 확인 (5분마다 실행)"""
#     logger.info("▶ 일기 생성 조건 체크 시작")
#     try:
#         db = next(get_db())
#         # 모든 활성 유저 조회
#         users = db.query(User).all()

#         for user in users:
#             try:
#                 # Repository를 사용하여 조건 체크
#                 chat_repo = TodayChatMessageRepository()

#                 # 1. 오늘 사용자 채팅 토큰 수 확인
#                 combined_content, total_tokens = chat_repo.get_today_user_chat_content_and_tokens(user.id)

#                 # 2. 오늘 AI 생성 여부 확인 (source_type='ai')
#                 today_ai_diary = chat_repo.check_today_diary_by_source(user.id, 'ai')

            
#                 # AI 생성 조건 체크
#                 # 1. 오늘 사용자 채팅 토큰이 55개 이상
#                 # 2. 아직 오늘 AI로 일기를 생성하지 않았는지 확인
#                 if total_tokens >= 55 and not today_ai_diary:
#                     # Redis에 알림 발행
#                     message = {
#                         "type": "diary_available",
#                         "user_id": user.id,
#                         "message": "오늘의 일기를 생성할 수 있습니다!"
                      
#                     }
                    
#                     channel = f"user_{user.id}_diary"
#                     message_json = json.dumps(message)
                    
#                     print(f"📤 Redis 발행 시도: channel={channel}, message={message_json}")
                    
#                     try:
#                         result = redis_client.publish(channel, message_json)
#                         print(f"✅ Redis 발행 성공: channel={channel}, result={result} (구독자 수)")
#                         logger.info(f"✅ 일기 생성 알림 발행: user_id={user.id}, 토큰수={total_tokens}")
#                     except Exception as e:
#                         print(f"❌ Redis 발행 실패: {e}")
#                         logger.error(f"❌ Redis 발행 실패: user_id={user.id}, error={e}")
                        
#                 else:
#                     if today_ai_diary:
#                         logger.info(f"ℹ️ 이미 오늘 AI 일기 생성됨: user_id={user.id}")
#                     else:
#                         logger.info(f"ℹ️ 토큰수 부족: user_id={user.id}, 토큰수={total_tokens}")

#             except Exception as e:
#                 logger.error(f"❌ 유저 {user.id} 일기 조건 체크 실패: {e}")

#     except Exception as e:
#         logger.error(f"❌ 일기 조건 체크 실패: {e}")
#     finally:
#         db.close()

# 4) 다이어리 분석 스케줄러
# @celery.task
# def daily_diary_analysis():
#     """매일 19:00에 실행되는 다이어리 분석"""
#     logger.info("🕐 일일 다이어리 분석 시작")

#     now = datetime.now()  # 시스템 로컬 시간 사용 (KST)

#     try:
#         db = next(get_db())
#         # 모든 사용자 조회
#         users = db.query(User).all()

#         for user in users:
#             try:
#                 # 2. 토큰 수 체크
#                 chat_repo = TodayChatMessageRepository()
#                 combined_content, total_tokens = chat_repo.get_today_user_chat_content_and_tokens(user.id)

#                 if total_tokens < 250:  # 250 토큰으로 수정
#                     logger.info(f"❌ 토큰 수 부족: user_id={user.id}, tokens={total_tokens}")
#                     continue

#                 # 3. 오늘 분석 결과 있는지 확인
#                 today = now.strftime("%Y-%m-%d")
#                 existing = db.query(DiaryAnalysisReport).filter(
#                     DiaryAnalysisReport.user_id == user.id,
#                     DiaryAnalysisReport.date_str == today
#                 ).first()

#                 if existing:
#                     logger.info(f"ℹ️ 이미 오늘 분석 완료: user_id={user.id}")
#                     continue

#                 # 4. 조건 충족하면 service 실행
#                 service = DiaryAnalysisService(db)
#                 result = service.analyze_user_diary(user.id)

#                 if result:
#                     logger.info(f"✅ 다이어리 분석 완료: user_id={user.id}")
#                 else:
#                     logger.error(f"❌ 다이어리 분석 실패: user_id={user.id}")

#             except Exception as e:
#                 logger.error(f"❌ 사용자 {user.id} 분석 실패: {str(e)}")
#                 continue

#     except Exception as e:
#         logger.error(f"❌ 일일 다이어리 분석 실패: {str(e)}")
#     finally:
#         db.close()

#     logger.info("✅ 일일 다이어리 분석 완료")





# 5) 자정 알림 리셋 스케줄러
@celery.task
def daily_reset_notifications():
    """매일 자정에 알림 상태 리셋"""
    logger.info("🕛 자정 알림 리셋 시작")

    try:
        db = next(get_db())
        # 모든 사용자 조회
        users = db.query(User).all()

        for user in users:
            try:
                channel = f"user_{user.id}_diary"
                reset_message = {
                    "type": "diary_reset",
                    "user_id": user.id,
                    "message": "새로운 하루가 시작되었습니다!",
                    "priority": "high"
                }
                
                message_json = json.dumps(reset_message)
                result = redis_client.publish(channel, message_json)
                
                logger.info(f"✅ 사용자 {user.id} 알림 리셋 완료 - 구독자 수: {result}")
                
            except Exception as e:
                logger.error(f"❌ 사용자 {user.id} 알림 리셋 실패: {e}")

    except Exception as e:
        logger.error(f"❌ 자정 리셋 실패: {e}")
    finally:
        db.close()

    logger.info("✅ 자정 알림 리셋 완료")

@celery.task
def check_encouragement_conditions_periodic():
    """격려 메시지 생성 조건 확인 (5분마다 실행)"""
    logger.info("▶ 격려 메시지 생성 조건 체크 시작")
    try:
        db = next(get_db())
        # 모든 활성 유저 조회
        users = db.query(User).all()

        for user in users:
            try:
                # # 1. 현재 시간이 23시 이후인지 확인
                # now = datetime.now()
                # if now.hour < 22:
                #     logger.info(f"ℹ️ 아직 22시 이전: user_id={user.id}, 현재시간={now.hour}시")
                #     continue

                # 2. 오늘 날짜로 encouragement_report 조회
                today = date.today()
                existing_encouragement = db.query(EncouragementReport).filter(
                    EncouragementReport.user_id == user.id,
                    func.date(EncouragementReport.timestamp) == today
                ).first()

                if existing_encouragement:
                    logger.info(f"ℹ️ 이미 오늘 격려 메시지 생성됨: user_id={user.id}")
                    continue

                # 3. Repository에서 user token 확인 (100 이상인지)
                chat_repo = TodayChatMessageRepository()
                combined_content, total_tokens = chat_repo.get_today_user_chat_content_and_tokens(user.id)

                if total_tokens < 100:
                    logger.info(f"❌ 토큰 수 부족: user_id={user.id}, tokens={total_tokens}")
                    continue

                # 4. 모든 조건 만족 시 서비스 호출
                logger.info(f"✅ 격려 메시지 생성 조건 만족: user_id={user.id}, tokens={total_tokens}")
                service = EncourageDiaryService(db)
                result = service.create_encouragement(user.id)
                
                if result:
                    logger.info(f"✅ 격려 메시지 생성 완료: user_id={user.id}")
                else:
                    logger.error(f"❌ 격려 메시지 생성 실패: user_id={user.id}")

            except Exception as e:
                logger.error(f"❌ 유저 {user.id} 격려 조건 체크 실패: {e}")

    except Exception as e:
        logger.error(f"❌ 격려 조건 체크 실패: {e}")
    finally:
        db.close()

# 6) 스케줄 설정
celery.conf.beat_schedule = {
    'check-diary-conditions': {
        'task': 'app.services.celery_app.check_diary_conditions_periodic',
        'schedule':300.0,  # 5분마다
    },
    'check-encouragement-conditions': {
        'task': 'app.services.celery_app.check_encouragement_conditions_periodic',
        'schedule': 300.0,  # 5분마다
    },
    # 'daily-diary-analysis': {
    #     'task': 'app.services.celery_app.daily_diary_analysis',
    #     'schedule': 300.0,  # 매일 23:00 정확히
    # },
    'daily-reset-notifications': {
        'task': 'app.services.celery_app.daily_reset_notifications',
        'schedule': crontab(hour=0, minute=0),  # 매일 00:00 정확히
    },
}
