from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.websocket_service import websocket_service
from app.api.dependencies.auth_dependencies import get_current_user
from app.models.db.user_model import User
import json

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: int
):
    """WebSocket 연결 엔드포인트"""
    try:
        # WebSocket 연결
        await websocket_service.connect(websocket, user_id)
        
        # 연결 유지
        while True:
            # 클라이언트로부터 메시지 수신 (연결 유지용)
            data = await websocket.receive_text()
            
            # 간단한 ping-pong 응답
            await websocket.send_text(json.dumps({
                "type": "pong",
                "message": "연결 유지됨"
            }))
            
    except WebSocketDisconnect:
        # 연결 해제
        await websocket_service.disconnect(user_id)
        print(f"❌ WebSocket 연결 해제: user_id={user_id}")
    except Exception as e:
        print(f"❌ WebSocket 에러: {e}")
        await websocket_service.disconnect(user_id) 