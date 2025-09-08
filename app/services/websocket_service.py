import asyncio
import json
import redis.asyncio as redis
from fastapi import WebSocket
from typing import Dict
from app.config.settings import settings

class WebSocketService:
    def __init__(self):
        print(f"🔗 WebSocket Service Redis 연결 시도: {settings.redis_host}:{settings.redis_port}")
        self.redis_client = redis.Redis(
            host=settings.redis_host, 
            port=settings.redis_port, 
            db=settings.redis_db
        )
        self.active_connections: Dict[int, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """WebSocket 연결 수락"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"✅ WebSocket 연결됨: user_id={user_id}")
        
        # Redis 구독 시작
        await self.subscribe_to_notifications(user_id, websocket)
        
    async def disconnect(self, user_id: int):
        """WebSocket 연결 해제"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"❌ WebSocket 연결 해제: user_id={user_id}")
            
    async def is_websocket_connected(self, websocket: WebSocket) -> bool:
        """WebSocket 연결 상태 확인"""
        try:
            # WebSocket 상태 확인 - 더 정확한 방법
            if hasattr(websocket, 'client_state'):
                return websocket.client_state.value == 1  # CONNECTED 상태
            elif hasattr(websocket, 'application_state'):
                # Starlette WebSocket 상태 확인
                from starlette.websockets import WebSocketState
                return websocket.application_state == WebSocketState.CONNECTED
            else:
                # 기본적인 연결 상태 확인
                return True
        except Exception as e:
            print(f"⚠️ WebSocket 상태 확인 실패: {e}")
            return False
            
    async def handle_connection_error(self, websocket: WebSocket, user_id: int = None):
        """연결 오류 처리"""
        try:
            print(f"🔌 WebSocket 연결 오류 처리 중...")
            if user_id and user_id in self.active_connections:
                del self.active_connections[user_id]
                print(f"🗑️ 연결 해제됨: user_id={user_id}")
        except Exception as e:
            print(f"❌ 연결 오류 처리 실패: {e}")
            
    async def subscribe_to_notifications(self, user_id: int, websocket: WebSocket):
        """Redis 구독하여 알림 수신"""
        try:
            print(f"🔍 Redis 구독 시작 준비: user_id={user_id}")
            pubsub = self.redis_client.pubsub()
            
            # 유저별 채널들 구독
            channels = [
                f"user_{user_id}_diary",      # 일기 알림
                f"user_{user_id}_plant",      # 식물 생성 알림
                f"user_{user_id}_report",     # 7일 레포트 알림
                f"user_{user_id}_wrapup",     # 하루 마무리 알림
                f"user_{user_id}_encourage"   # 격려 메시지 알림
            ]
            
            print(f"📡 구독할 채널들: {channels}")
            await pubsub.subscribe(*channels)
            
            print(f"🎯 Redis 구독 시작: user_id={user_id}")
            
            async for message in pubsub.listen():
                print(f"📨 Redis 메시지 수신: {message}")
                
                if message['type'] == 'message':
                    try:
                        # 메시지 파싱
                        data = json.loads(message['data'])
                        channel = message['channel'].decode('utf-8')  # bytes를 str로 변환
                        
                        print(f"🔍 메시지 파싱 완료: channel={channel}, data={data}")
                        
                        # 채널별 메시지 처리
                        if channel == f"user_{user_id}_diary":
                            print(f"📝 일기 알림 처리: {data}")
                            print(f"🔍 일기 알림 타입: {data.get('type')}")
                            
                            # WebSocket 연결 상태 재확인
                            if not await self.is_websocket_connected(websocket):
                                print(f"⚠️ WebSocket 연결 불안정 - 메시지 처리 건너뜀: {data.get('type')}")
                                continue
                            
                            # diary_unavailable 처리 추가
                            if data.get('type') == 'diary_unavailable':
                                print(f"🛑 diary_unavailable 처리: {data}")
                                await self.send_notification(websocket, {
                                    "type": "diary_unavailable",
                                    "target": "blink-study-overlay-monitor",
                                    "message": "일기 생성이 완료되었습니다!",
                                    "priority": data.get("priority", "normal"),
                                    "reason": data.get("reason", "")
                                }, user_id)


                            # diary_reset 처리 추가
                            elif data.get('type') == 'diary_reset':
                                print(f"🕛 diary_reset 처리: {data}")
                                await self.send_notification(websocket, {
                                    "type": "diary_reset",
                                    "target": "global-notification-manager",
                                    "message": data.get("message", "새로운 하루가 시작되었습니다!"),
                                    "priority": data.get("priority", "high")
                                }, user_id)


                            else:
                                # 기존 diary_available 처리
                                await self.send_notification(websocket, {
                                    "type": "diary_available",
                                    "target": "blink-study-overlay-monitor",
                                    "message": data.get("message", "일기 생성이 가능합니다!")
                                }, user_id)


                        elif channel == f"user_{user_id}_plant":
                            print(f"🌱 식물 알림 처리: {data}")
                            await self.send_notification(websocket, {
                                "type": "plant_generation",
                                "target": "garden-section",
                                "message": "새로운 식물이 생성되었습니다!"
                            }, user_id)


                        elif channel == f"user_{user_id}_report":
                            print(f"📊 리포트 알림 처리: {data}")
                            
                            # similar_pattern_event_check에서 발행하는 최종 리포트 처리
                            if data.get('type') == 'report':
                                print(f"📋 최종 리포트 완성 알림 처리: {data}")
                                await self.send_notification(websocket, {
                                    "type": "final_report",
                                    "target": "study-section",
                                    "message": data.get("message", "최종리포트 완성!"),
                                    "report_id": data.get("report_id")
                                }, user_id)
                            else:
                                # 기존 7일 리포트 처리
                                await self.send_notification(websocket, {
                                    "type": "seven_day_report",
                                    "target": "study-section",
                                    "message": "7일 감정 레포트가 완성되었습니다!",
                                    "analysis_id": data.get("analysis_id"),
                                    "week_start_date": data.get("week_start_date"),
                                    "week_end_date": data.get("week_end_date")
                                }, user_id)

                        elif channel == f"user_{user_id}_chart":
                            print(f"📈 차트 로딩 완료 알림 처리: {data}")
                            await self.send_notification(websocket, {
                                "type": "chart_loading_complete",
                                "target": "study-section",
                                "message": "7일 리포트 차트 로딩이 완료되었습니다!",
                                "analysis_id": data.get("analysis_id"),
                                "week_start_date": data.get("week_start_date"),
                                "week_end_date": data.get("week_end_date")
                            }, user_id)


                        elif channel == f"user_{user_id}_wrapup":
                            print(f"🌅 마무리 알림 처리: {data}")
                            await self.send_notification(websocket, {
                                "type": "daily_wrapup",
                                "target": "main-dashboard",
                                "message": "하루 마무리 시간입니다!"
                            }, user_id)

                        elif channel == f"user_{user_id}_encourage":
                            print(f"💌 격려 메시지 알림 처리: {data}")
                            
                            # encourage_unavailable 처리 추가
                            if data.get('type') == 'encourage_unavailable':
                                print(f"🛑 encourage_unavailable 처리: {data}")
                                await self.send_notification(websocket, {
                                    "type": "encourage_unavailable",
                                    "target": "letter-overlay-glow",
                                    "message": "응원격려 확인함"
                                }, user_id)
                            else:
                                # 기존 encourage_available 처리
                                await self.send_notification(websocket, {
                                    "type": "encourage_available",
                                    "target": "letter-overlay-glow",
                                    "message": "오늘 하루도 수고했어요, 당신에게 편지가 왔어요"
                                }, user_id)
                            
                        else:
                            print(f"❓ 알 수 없는 채널: {channel}")
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON 파싱 실패: {e}, 원본 메시지: {message}")
                    except Exception as e:
                        print(f"❌ 메시지 처리 실패: {e}")
                elif message['type'] == 'subscribe':
                    print(f"✅ Redis 구독 성공: {message}")
                elif message['type'] == 'unsubscribe':
                    print(f"❌ Redis 구독 해제: {message}")
                else:
                    print(f"📡 Redis 메시지 타입: {message['type']}")
                        
        except Exception as e:
            print(f"❌ Redis 구독 실패: {e}")
        finally:
            print(f"🔌 Redis 구독 종료: user_id={user_id}")
            await pubsub.close()
            
    async def send_notification(self, websocket: WebSocket, data: dict, user_id: int = None):
        """WebSocket으로 프론트에 알림 전송"""
        try:
            # WebSocket 연결 상태 확인
            if await self.is_websocket_connected(websocket):
                await websocket.send_text(json.dumps(data))
                print(f"📤 알림 전송 성공: {data['type']}")
            else:
                print(f"⚠️ WebSocket 연결 상태 불량 - 메시지 전송 건너뜀: {data['type']}")
                if user_id:
                    await self.handle_connection_error(websocket, user_id)
                    
        except Exception as e:
            print(f"❌ 알림 전송 실패: {e}")
            # WebSocket이 닫힌 상태에서 발생하는 특정 오류 처리
            if "Cannot call" in str(e) and "close message" in str(e):
                print(f"🔄 WebSocket이 닫힌 상태 - 연결 재설정 필요: {data['type']}")
                if user_id:
                    await self.handle_connection_error(websocket, user_id)
            else:
                print(f"❌ 기타 WebSocket 오류: {e}")
                if user_id:
                    await self.handle_connection_error(websocket, user_id)

# 전역 인스턴스
websocket_service = WebSocketService() 