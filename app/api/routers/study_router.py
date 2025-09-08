from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.api.dependencies.auth_dependencies import get_current_user
from app.services.diary_service import DiaryService
from app.services.encourage_diary_service import EncourageDiaryService
from app.repositories.today_chat_message_repository import TodayChatMessageRepository
from app.models.schemas.study_schema import DiaryResponse
from app.models.db.user_model import User
from app.models.db.study_model import DiaryReport, EncouragementReport, WeeklyAnalysisReport, DiaryAnalysisReport
from app.core.connection import get_db
from sqlalchemy.orm import Session
from datetime import datetime, date
import json
import redis
from app.config.settings import settings
from sqlalchemy import func

router = APIRouter(prefix="/study", tags=["study"])

# 일기 생성 스트리밍 라우터 -- sub diary generat 버튼이랑 호출출
@router.post("/diary/generate/stream")
async def generate_diary_stream(
    current_user: User = Depends(get_current_user),
    diary_service: DiaryService = Depends()
):
    try:
        # Repository 직접 호출
        chat_repository = TodayChatMessageRepository()
        
        # 오늘 AI 생성 여부 확인 (source_type='ai')
        today_ai_diary = chat_repository.check_today_diary_by_source(current_user.id, 'ai')
        if today_ai_diary:
            raise HTTPException(
                status_code=400, 
                detail="오늘 이미 AI로 생성한 일기가 있습니다."
            )
        
        # 오늘 사용자 채팅 토큰수 확인
        formatted_chats, total_tokens = chat_repository.diary_get_today_user_chat_and_tokens(current_user.id)
        min_tokens = 55  # 최소 토큰수 설정
        if total_tokens < min_tokens:
            raise HTTPException(
                status_code=400, 
                detail=f"일기 생성하기엔 오늘의 채팅수가 부족합니다"
            )
        
        return StreamingResponse(
            diary_service.generate_diary_stream(current_user.id),
            media_type="text/plain"
        )
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 생성 실패: {str(e)}")


# async def generate_diary_stream(
#     current_user: User = Depends(get_current_user),
#     diary_service: DiaryService = Depends()
# ):
#     try:
#         # Repository 직접 호출
#         chat_repository = TodayChatMessageRepository()
        
#         # 오늘 AI 생성 여부 확인 (source_type='ai')
#         today_ai_diary = chat_repository.check_today_diary_by_source(current_user.id, 'ai')
#         if today_ai_diary:
#             raise HTTPException(
#                 status_code=400, 
#                 detail="오늘 이미 AI로 생성한 일기가 있습니다."
#             )
        
#         # 오늘 사용자 채팅 토큰 수 확인
#         combined_content, total_tokens = chat_repository.get_today_user_chat_content_and_tokens(current_user.id)
#         min_tokens = 55  # 최소 토큰 수 설정
#         if total_tokens < min_tokens:
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"일기 생성하기엔 오늘의 채팅 토큰이 부족합니다 (현재: {total_tokens}개, 필요: {min_tokens}개)"
#             )
        
#         return StreamingResponse(
#             diary_service.generate_diary_stream(current_user.id),
#             media_type="text/plain"
#         )
#     except HTTPException:
#         # HTTPException은 그대로 전달
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"일기 생성 실패: {str(e)}")




















# 사용자 직접 일기 저장 라우터
@router.post("/user/diary/save")
async def save_user_diary(
    diary_data: dict,
    current_user: User = Depends(get_current_user)
):
    try:
        # Repository 직접 호출
        chat_repository = TodayChatMessageRepository()
        
        # 오늘 사용자 직접 작성 여부 확인 (source_type='user')
        today_user_diary = chat_repository.check_today_diary_by_source(current_user.id, 'user')
        if today_user_diary:
            raise HTTPException(
                status_code=400, 
                detail="오늘 이미 직접 작성한 일기가 있습니다."
            )
        
        # DB에 직접 저장
        db = next(get_db())
        try:
            diary_report = DiaryReport(
                user_id=current_user.id,
                content=diary_data.get('content'),
                source_type='user',  # 사용자 직접 작성은 항상 'user'
                timestamp=datetime.now()  # 시스템 로컬 시간 사용 (KST)
            )
            db.add(diary_report)
            db.commit()
            
            return {"message": "일기가 성공적으로 저장되었습니다."}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"일기 저장 실패: {str(e)}")
        finally:
            db.close()
            
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 저장 실패: {str(e)}")


# 일기 생성 조건 체크 라우터
@router.get("/diary/check-condition")
async def check_diary_condition(
    current_user: User = Depends(get_current_user)
):
    try:
        # Repository 직접 호출
        chat_repository = TodayChatMessageRepository()
        
        # 오늘 AI 생성 여부 확인 (source_type='ai')
        today_ai_diary = chat_repository.check_today_diary_by_source(current_user.id, 'ai')
        if today_ai_diary:
            return {
                "available": False,
                "reason": "오늘 이미 AI로 생성한 일기가 있습니다."
            }
        
        # 오늘 사용자 채팅 토큰수 확인
        formatted_chats, total_tokens = chat_repository.diary_get_today_user_chat_and_tokens(current_user.id)
        min_tokens = 55  # 최소 토큰수 설정
        if total_tokens < min_tokens:
            return {
                "available": False,
                "reason": f"일기 생성하기엔 오늘의 채팅수가 부족합니다."
            }
        
        return {
            "available": True,
            "reason": "일기 생성이 가능합니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조건 확인 실패: {str(e)}")




# async def check_diary_condition(
#     current_user: User = Depends(get_current_user)
# ):
#     try:
#         # Repository 직접 호출
#         chat_repository = TodayChatMessageRepository()
        
#         # 오늘 AI 생성 여부 확인 (source_type='ai')
#         today_ai_diary = chat_repository.check_today_diary_by_source(current_user.id, 'ai')
#         if today_ai_diary:
#             return {
#                 "available": False,
#                 "reason": "오늘 이미 AI로 생성한 일기가 있습니다."
#             }
        
#         # 오늘 사용자 채팅 토큰 수 확인
#         combined_content, total_tokens = chat_repository.get_today_user_chat_content_and_tokens(current_user.id)
#         min_tokens = 55  # 최소 토큰 수 설정
#         if total_tokens < min_tokens:
#             return {
#                 "available": False,
#                 "reason": f"일기 생성하기엔 오늘의 채팅 토큰이 부족합니다. (현재: {total_tokens}개, 필요: {min_tokens}개)"
#             }
        
#         return {
#             "available": True,
#             "reason": "일기 생성이 가능합니다."
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"조건 확인 실패: {str(e)}")
    



# 일기 목록 조회 라우터
@router.get("/diary/list")
async def get_diary_list(
    current_user: User = Depends(get_current_user)
):
    try:
        # Repository 직접 호출
        chat_repository = TodayChatMessageRepository()
        
        # 사용자의 모든 일기 조회 (최신순)
        diaries = chat_repository.get_user_diaries(current_user.id)
        
        # JS에서 기대하는 형태로 변환
        diary_list = []
        for diary in diaries:
            diary_list.append({
                "id": diary.diary_id,  # primary key는 diary_id
                "content": diary.content,
                "source_type": diary.source_type,  # 'user' 또는 'ai'
                "timestamp": diary.timestamp.isoformat() if diary.timestamp else None,
                "user_id": diary.user_id
            })
        
        return diary_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 목록 조회 실패: {str(e)}")

# 개별 일기 조회 라우터
@router.get("/diary/{diary_id}")
async def get_diary_detail(
    diary_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        # Repository 직접 호출
        chat_repository = TodayChatMessageRepository()
        
        # 특정 일기 조회 (사용자 본인의 일기만)
        diary = chat_repository.get_diary_by_id(diary_id, current_user.id)
        
        if not diary:
            raise HTTPException(
                status_code=404, 
                detail="일기를 찾을 수 없습니다."
            )
        
        # JS에서 기대하는 형태로 변환
        return {
            "id": diary.diary_id,
            "content": diary.content,
            "source_type": diary.source_type,
            "timestamp": diary.timestamp.isoformat() if diary.timestamp else None,
            "user_id": diary.user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 조회 실패: {str(e)}")


@router.get("/encourage/check-condition")
async def check_encourage_condition(
    current_user: User = Depends(get_current_user)
):
    try:
        # 오늘 응원 메시지 존재 여부 확인
        today = date.today()
        print(f"🔍 [DEBUG] today: {today}, type: {type(today)}")
        
        db = next(get_db())
        
        try:
            # 먼저 모든 응원 메시지 조회해서 디버깅
            all_encouragements = db.query(EncouragementReport).filter(
                EncouragementReport.user_id == current_user.id
            ).all()
            
            print(f"🔍 [DEBUG] 사용자의 모든 응원 메시지 수: {len(all_encouragements)}")
            for enc in all_encouragements:
                print(f"🔍 [DEBUG] 응원 메시지 ID: {enc.encouragement_id}, timestamp: {enc.timestamp}, date: {enc.timestamp.date() if enc.timestamp else None}")
            
            # 실제 쿼리 실행
            existing_encouragement = db.query(EncouragementReport).filter(
                EncouragementReport.user_id == current_user.id,
                func.date(EncouragementReport.timestamp) == today
            ).first()
            
            print(f"🔍 [DEBUG] 오늘 응원 메시지 존재 여부: {existing_encouragement is not None}")
            
            if existing_encouragement:
                return {
                    "available": False,
                    "reason": "오늘의 응원 메시지가 이미 존재합니다."
                }
            
            # 응원 메시지가 없으면 채팅 부족 메시지 반환
            return {
                "available": False,
                "reason": "오늘 응원 메시지 생성하기엔 채팅이 부족합니다."
            }
            
        except Exception as e:
            print(f"❌ [DEBUG] 데이터베이스 쿼리 에러: {str(e)}")
            print(f"❌ [DEBUG] 에러 타입: {type(e).__name__}")
            import traceback
            print(f"❌ [DEBUG] 스택 트레이스: {traceback.format_exc()}")
            db.rollback()
            raise e
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ [DEBUG] 전체 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 오늘의 응원 메시지 조회 라우터
@router.get("/encourage")
async def get_today_encouragement(
    current_user: User = Depends(get_current_user)
):
    try:
        # 오늘 날짜로 생성된 응원 메시지 조회
        today = date.today()
        print(f"🔍 [DEBUG] 오늘 날짜: {today}")
        
        db = next(get_db())
        
        try:
            # 오늘 날짜로 생성된 응원 메시지 조회
            today_encouragement = db.query(EncouragementReport).filter(
                EncouragementReport.user_id == current_user.id,
                func.date(EncouragementReport.timestamp) == today
            ).first()
            
            print(f"🔍 [DEBUG] 오늘 응원 메시지 존재 여부: {today_encouragement is not None}")
            
            if not today_encouragement:
                raise HTTPException(
                    status_code=404, 
                    detail="오늘의 응원 메시지가 없습니다."
                )
            
            # encourage_content만 추출해서 반환
            response_data = {
                "encourage_content": today_encouragement.encourage_content
            }
            
            # Redis에 encourage_unavailable 메시지 발행
            try:
                redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db
                )
                
                message = {
                    "type": "encourage_unavailable",
                    "target": "letter-overlay-glow",
                    "message": "응원격려 확인함"
                }
                
                channel = f"user_{current_user.id}_encourage"
                message_json = json.dumps(message)
                
                print(f"📤 [DEBUG] Redis 발행 시도: channel={channel}, message={message_json}")
                result = redis_client.publish(channel, message_json)
                print(f"✅ [DEBUG] Redis 발행 성공: channel={channel}, result={result} (구독자 수)")
                
            except Exception as e:
                print(f"❌ [ERROR] Redis 발행 실패: {e}")
                # Redis 발행 실패는 치명적이지 않으므로 예외를 다시 발생시키지 않음
            
            return response_data
            
        except HTTPException:
            # HTTPException은 그대로 전달
            raise
        except Exception as e:
            print(f"❌ [DEBUG] 데이터베이스 쿼리 에러: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"응원 메시지 조회 실패: {str(e)}")
        finally:
            db.close()
            
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        print(f"❌ [DEBUG] 전체 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"응원 메시지 조회 실패: {str(e)}")


# 7일 감정 리포트 데이터 조회
@router.get("/seven-day-report/{analysis_id}")
async def get_seven_day_report(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        print(f"📊 7일 리포트 데이터 조회 시작: analysis_id={analysis_id}, user_id={current_user.id}")
        
        # weekly_analysis_report 테이블에서 데이터 조회
        weekly_data = db.query(WeeklyAnalysisReport).filter(
            WeeklyAnalysisReport.analysis_id == analysis_id,
            WeeklyAnalysisReport.user_id == current_user.id
        ).first()
        
        if not weekly_data:
            raise HTTPException(status_code=404, detail="7일 리포트 데이터를 찾을 수 없습니다.")
        
        print(f"🔍 weekly_data 조회 성공: week_start_date={weekly_data.week_start_date}, week_end_date={weekly_data.week_end_date}")
        
        # diary_analysis_report 테이블에서 데이터 조회 (date_str 사용)
        diary_data = db.query(DiaryAnalysisReport).filter(
            DiaryAnalysisReport.user_id == current_user.id,
            DiaryAnalysisReport.date_str >= weekly_data.week_start_date.strftime("%Y-%m-%d"),
            DiaryAnalysisReport.date_str <= weekly_data.week_end_date.strftime("%Y-%m-%d")
        ).all()
        
        print(f"🔍 diary_data 조회 완료: {len(diary_data)}개 일기 분석")
        
        # weekly_data 상세 출력
        print(f"📊 weekly_data.analysis_id: {weekly_data.analysis_id}")
        print(f"📊 weekly_data.emotion_trend_result: {weekly_data.emotion_trend_result}")
        print(f"📊 weekly_data.keyword_pattern_result: {weekly_data.keyword_pattern_result}")
        print(f"📊 weekly_data.comprehensive_pattern_result: {weekly_data.comprehensive_pattern_result}")
        
        # diary_data 첫 번째 항목 상세 출력
        if diary_data:
            first_diary = diary_data[0]
            print(f"📊 첫 번째 diary_data.report_id: {first_diary.report_id}")
            print(f"📊 첫 번째 diary_data.emotions: {first_diary.emotions}")
            print(f"📊 첫 번째 diary_data.scores: {first_diary.scores}")
            print(f"📊 첫 번째 diary_data.keywords: {first_diary.keywords}")
            print(f"📊 첫 번째 diary_data.summary: {first_diary.summary}")
        
        # 응답 데이터 구성
        response_data = {
            "weekly_analysis": {
                "id": weekly_data.analysis_id,
                "start_date": weekly_data.week_start_date.strftime("%m-%d"),
                "end_date": weekly_data.week_end_date.strftime("%m-%d"),
                "emotion_trend": weekly_data.emotion_trend_result,
                "keyword_patterns": weekly_data.keyword_pattern_result,
                "comprehensive_pattern_result": weekly_data.comprehensive_pattern_result,
                "overall_assessment": weekly_data.comprehensive_pattern_result.get("overall_assessment", "분석 중") if weekly_data.comprehensive_pattern_result else "분석 중"
            },
            "diary_analyses": [
                {
                    "id": diary.report_id,
                    "date_str": diary.date_str,
                    "emotions": diary.emotions,
                    "scores": diary.scores,
                    "keywords": diary.keywords,
                    "keyword_descriptions": diary.keyword_descriptions,
                    "summary": diary.summary
                }
                for diary in diary_data
            ]
        }
        
        print(f"📤 최종 응답 데이터 구성 완료:")
        print(f"📤 response_data.weekly_analysis: {response_data['weekly_analysis']}")
        print(f"📤 response_data.diary_analyses 개수: {len(response_data['diary_analyses'])}")
        print(f"✅ 7일 리포트 데이터 조회 완료: {len(diary_data)}개 일기 분석 포함")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 7일 리포트 데이터 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"7일 리포트 데이터 조회 실패: {str(e)}")


# 차트 로딩 완료 알림
@router.post("/chart-loading-complete")
async def chart_loading_complete(
    data: dict,
    current_user: User = Depends(get_current_user)
):
    try:
        print(f"📤 차트 로딩 완료 알림 수신: {data}")
        
        # Redis에 구독 발행 (study/section.js가 받을 알림)
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db
        )
        
        message = {
            "type": "chart_loading_complete",
            "target": "study-section",
            "message": "7일 리포트 차트 로딩이 완료되었습니다.",
            "analysis_id": data.get("analysis_id"),
            "week_start_date": data.get("week_start_date"),
            "week_end_date": data.get("week_end_date")
        }
        
        channel = f"user_{current_user.id}_chart"
        message_json = json.dumps(message)
        
        print(f"📤 Redis 발행: channel={channel}, message={message_json}")
        result = redis_client.publish(channel, message_json)
        print(f"✅ Redis 발행 성공: result={result} (구독자 수)")
        
        return {"status": "success", "message": "차트 로딩 완료 알림이 전송되었습니다."}
        
    except Exception as e:
        print(f"❌ 차트 로딩 완료 알림 전송 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"차트 로딩 완료 알림 전송 실패: {str(e)}")