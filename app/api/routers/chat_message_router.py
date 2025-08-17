from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.connection import get_db
from app.api.dependencies.auth_dependencies import get_current_user
from app.models.db.user_model import User
import logging
from app.services.chat_service import save_user_message, save_gpt_response
from app.prompt.chat_prompt import build_chat_prompt
from app.models.schemas.chat_schema import MessageInput
from app.models.schemas.chat_schema import TurnInput
from fastapi import HTTPException
from app.clients.gpt_api import stream_gpt_response
from fastapi.responses import StreamingResponse
from fastapi import Request
from app.services.session_create import get_or_create_session_id
import logging
from app.models.db.chat_message_model import ChatMessage
from datetime import datetime
from app.api.dependencies.auth_dependencies import get_current_user
from app.utils.time_utils import get_kst_now
from app.services.diary_service import DiaryService
import json
import redis
from app.config.settings import settings


router = APIRouter()


# 채팅 메시지 저장
@router.post("/chat/send")
def send_message(
    data: MessageInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 20분 기준 반영된 세션 ID 조회/생성
        session_id = get_or_create_session_id(db, current_user.id)
        print(f"✅ [routers. /chat/send ] , session_id {session_id} ")

        # 메시지 저장 (session_id 포함)
        turn = save_user_message(
            db, current_user.id, data.message, session_id=session_id
        )
        print(f"turn : {turn} ")


        # turn과 session_id를 함께 반환
        return {
            "turn": turn,
            "session_id": session_id
        }
    except Exception as e:
        print("❌ /chat/send 에러:", str(e))
        raise HTTPException(status_code=500, detail="채팅 메시지 저장 실패")



# GPT 스트리밍 응답 생성 & 저장 

logger = logging.getLogger(__name__)

@router.post("/chat/response_stream")
async def stream_response(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 요청 바디 파싱
        body = await request.json()
        turn = body.get("turn")
        session_id = body.get("session_id")  # 프론트에서 넘어오는 세션 ID

        logger.info(
            f"✅ /chat/response_stream start - user_id={current_user.id}, turn={turn}, session_id={session_id}"
        )

        # 프롬프트 구성
        prompt = build_chat_prompt(db, current_user.id, turn, session_id=session_id)
        logger.debug(f"Prompt built: {prompt}")

        async def event_generator():
            accumulated = ""
            try:
                # 스트리밍 청크 전송
                async for chunk in stream_gpt_response(prompt):
                    accumulated += chunk
                    yield chunk

            except Exception as stream_err:
                # 스트리밍 중 오류 발생
                logger.error(
                    f"❌ Error during streaming: {stream_err}", exc_info=True
                )
                # 클라이언트에 오류 알림
                yield "[Error] GPT 스트리밍 중 오류가 발생했습니다."
                return

            # 스트리밍 완료 시 저장
            try:
                logger.info(
                    f"✅ Streaming complete (total_len={len(accumulated)}). Saving to DB."
                )
                save_gpt_response(
                    db, current_user.id, accumulated, turn, session_id=session_id
                )
                
            except Exception as save_err:
                logger.error(
                    f"❌ Error saving GPT response: {save_err}", exc_info=True
                )
                return

            # 조건 체크 및 Redis 발행 (try 블록 밖으로)
            logger.info("🔍 save_gpt_response 완료, 조건 체크 시작")
            
            try:
                logger.info("🔍 DiaryService 생성 시작")
                diary_service = DiaryService()
                logger.info("✅ DiaryService 생성 완료")
                
                logger.info("🔍 조건 체크 함수 호출 시작")
                condition_result = await diary_service.check_diary_conditions(current_user.id)
                logger.info(f"🔍 조건 체크 결과: {condition_result}")
                
                if condition_result["available"]:
                    logger.info("🔍 available: true, Redis 발행 시작")
                    # Redis 발행 (websocket_service.py와 동일한 형태)
                    redis_client = redis.Redis(
                        host=settings.redis_host,
                        port=settings.redis_port,
                        db=settings.redis_db
                    )
                    
                    message = {
                        "type": "diary_available",
                        "target": "blink-study-overlay-monitor",
                        "message": "일기 생성이 가능합니다!"
                    }
                    
                    channel = f"user_{current_user.id}_diary"
                    message_json = json.dumps(message)
                    
                    logger.info(f"🔍 Redis 발행 시도: channel={channel}, message={message_json}")
                    result = redis_client.publish(channel, message_json)
                    logger.info(f"✅ response streaml   Redis 발행 성공: channel={channel}, result={result}")
                else:
                    logger.info(f"🔍 available: false, Redis 발행 건너뜀")
                    
            except Exception as check_err:
                logger.error(f"❌ 일기 조건 체크 실패: {check_err}")

        return StreamingResponse(event_generator(), media_type="text/plain")

    except Exception as e:
        logger.error(f"❌ /chat/response_stream error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="GPT 스트리밍 응답 처리 실패")

# /chat/history 라우터 :  채팅내용 렌더링하기 
from pydantic import BaseModel
class DateRequest(BaseModel):
    date: str


@router.post("/chat/history")

def get_chat_history(req: DateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)):
    """
    오늘 날짜 기준 채팅 기록 조회
    """

    # 문자열 날짜 → datetime.date 변환 (KST 기준)
    try:
        target_date = datetime.strptime(req.date, "%Y-%m-%d").date()
    except ValueError:
        return {"messages": []}

    # KST 기준으로 시작/끝 시간 설정
    from datetime import timezone, timedelta
    kst = timezone(timedelta(hours=9))
    start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=kst)
    end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=kst)

    records = db.query(ChatMessage).filter(
        ChatMessage.user_id == user.id,
        ChatMessage.timestamp >= start,
        ChatMessage.timestamp <= end
    ).order_by(ChatMessage.timestamp.asc()).all()

    messages = [
      {
        "role": r.role, 
        "message": r.message,
        "timestamp": r.timestamp.isoformat()
      } 
      for r in records
    ]
    return {"messages": messages}


# 채팅 목록 조회 (날짜별 그룹화)
@router.get("/chat/list")
def get_chat_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 현재 유저의 모든 채팅 메시지 조회
        records = db.query(ChatMessage).filter(
            ChatMessage.user_id == current_user.id
        ).order_by(ChatMessage.timestamp.desc()).all()
        
        # timestamp에서 날짜 추출하여 그룹화
        chat_dates = set()
        for record in records:
            date_str = record.timestamp.strftime("%Y-%m-%d")
            chat_dates.add(date_str)
        
        # 날짜순으로 정렬 (최신순)
        sorted_dates = sorted(list(chat_dates), reverse=True)
        
        return {"chat_dates": sorted_dates}
        
    except Exception as e:
        print("❌ /chat/list 에러:", str(e))
        raise HTTPException(status_code=500, detail="채팅 목록 조회 실패")
