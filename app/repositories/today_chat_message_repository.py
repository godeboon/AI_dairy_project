from app.models.db.chat_message_model import ChatMessage
from app.models.db.study_model import DiaryReport
from sqlalchemy import func
from datetime import datetime, date
from app.core.connection import get_db
from app.utils.time_utils import get_kst_now

class TodayChatMessageRepository:
    def get_today_chats(self, user_id: int):
        """오늘 날짜의 채팅 데이터를 role 구분하여 조회"""
        db = next(get_db())
        try:
            today = get_kst_now().date()
            chats = db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id,
                ChatMessage.timestamp >= today
            ).order_by(ChatMessage.timestamp.asc()).all()
            return chats
        finally:
            db.close()


    def diary_get_today_user_chat_and_tokens(self, user_id: int):
        """오늘의 user 채팅만 가져와서 포맷팅하고 토큰 수 계산"""
        db = next(get_db())
        try:
            today = get_kst_now().date()
            # user role만 조회
            user_chats = db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id,
                ChatMessage.role == "user",
                ChatMessage.timestamp >= today
            ).order_by(ChatMessage.timestamp.asc()).all()
            
            formatted_chats = []
            for chat in user_chats:
                formatted_chats.append(f"{chat.role}: {chat.message}")
            
            # 토큰 수 계산 (간단히 단어 수로 계산)
            total_tokens = sum(len(chat.message.split()) for chat in user_chats)
            
            return formatted_chats, total_tokens
        finally:
            db.close()

    
    def get_today_chats_by_role(self, user_id: int, role: str):
        """특정 role의 오늘 채팅 데이터 조회"""
        db = next(get_db())
        try:
            today = get_kst_now().date()
            chats = db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id,
                ChatMessage.role == role,
                ChatMessage.timestamp >= today
            ).order_by(ChatMessage.timestamp.asc()).all()
            return chats
        finally:
            db.close()
    
    def get_today_all_chats_formatted(self, user_id: int):
        """오늘의 모든 채팅을 role 구분하여 포맷팅"""
        db = next(get_db())
        try:
            today = get_kst_now().date()
            chats = db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id,
                ChatMessage.timestamp >= today
            ).order_by(ChatMessage.timestamp.asc()).all()
            
            formatted_chats = []
            for chat in chats:
                formatted_chats.append(f"{chat.role}: {chat.message}")
            
            return formatted_chats
        finally:
            db.close()
    
    def get_today_user_chat_content_and_tokens(self, user_id: int) -> tuple[str, int]:
        """오늘 날짜의 user 채팅 내용을 합치고 토큰 수 계산"""
        db = next(get_db())
        try:
            today = get_kst_now().date()
            # user role만 조회
            user_chats = db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id,
                ChatMessage.role == "user",
                ChatMessage.timestamp >= today
            ).order_by(ChatMessage.timestamp.asc()).all()
            
            # 채팅 내용을 하나로 합치기
            combined_content = " ".join([chat.message for chat in user_chats])
            
            # 토큰 수 계산 (간단히 단어 수로 계산)
            total_tokens = sum(len(chat.message.split()) for chat in user_chats)
            
            return combined_content, total_tokens
        finally:
            db.close()
    

    
    def check_today_diary(self, user_id: int) -> bool:
        """오늘 생성된 일기가 있는지 확인"""
        db = next(get_db())
        try:
            today = get_kst_now().date()
            existing_diary = (
                db.query(DiaryReport)
                .filter(
                    DiaryReport.user_id == user_id,
                    func.date(DiaryReport.timestamp) == today
                )
                .first()
            )
            return existing_diary is not None
        finally:
            db.close()
    
    def get_today_chat_count(self, user_id: int) -> int:
        """오늘 채팅 수 조회"""
        db = next(get_db())
        try:
            today = get_kst_now().date()
            chat_count = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.user_id == user_id,
                    ChatMessage.timestamp >= today
                )
                .count()
            )
            return chat_count
        finally:
            db.close()



    def check_today_diary_by_source(self, user_id: int, source_type: str) -> bool:
        """특정 source_type의 오늘 일기 존재 여부 확인"""
        db = next(get_db())
        try:
            today = get_kst_now().date()
            existing_diary = (
                db.query(DiaryReport)
                .filter(
                    DiaryReport.user_id == user_id,
                    DiaryReport.source_type == source_type,
                    func.date(DiaryReport.timestamp) == today
                )
                .first()
            )
            return existing_diary is not None
        finally:
            db.close()
    
    def get_user_diaries(self, user_id: int):
        """사용자의 모든 일기 조회 (최신순)"""
        db = next(get_db())
        try:
            diaries = (
                db.query(DiaryReport)
                .filter(DiaryReport.user_id == user_id)
                .order_by(DiaryReport.timestamp.desc())  # 최신순 정렬
                .all()
            )
            return diaries
        finally:
            db.close() 

    def today_session_user_chats_formatted(self, user_id: int, session_id: str):
        """특정 세션의 user 채팅만 포맷팅"""
        db = next(get_db())
        try:
            user_chats = db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id,
                ChatMessage.session_id == session_id,
                ChatMessage.role == "user"
            ).order_by(ChatMessage.turn.asc()).all()
            
            formatted_chats = []
            for chat in user_chats:
                formatted_chats.append(chat.message)  # role 제거, 메시지만 추가
            
            return formatted_chats
        finally:
            db.close()




