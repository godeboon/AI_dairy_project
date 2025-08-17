# services/summarization_service.py -> mixtral_logic

from sqlalchemy.orm import sessionmaker
from app.core.connection import engine
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.session_summary_repository import SessionSummaryRepository
from app.clients.mixtralclient import MixtralClient




SessionLocal = sessionmaker(bind=engine)

class SummarizationService:
    """
    [비즈니스 로직]
    - 요약이라는 도메인 로직 전체 흐름을 조율합니다.
    """

    def __init__(self):
        # HTTP 클라이언트 초기화
        self.client = MixtralClient()

    def summarize(self, user_id: int, session_id: str):
        # 1) DB 세션 열기
        db = SessionLocal()

        # 2) Repository 생성
        chat_repo    = ChatMessageRepository(db)
        summary_repo = SessionSummaryRepository(db)

        # ③ 이미 요약이 있으면 스킵(optional)
        if summary_repo.exists(user_id, session_id):
            db.close()
            print( "‼️ 이미 sessionsummary 요약된 것이 있음")
            return

        # 3) 메시지 조회
        msgs = chat_repo.list_by_session(user_id, session_id)

        # 1. 요약 지침 프롬프트 ([INST] 안에 들어갈 명령어)
        instruction = (
            "당신은 두 사람의 대화 내용을 간결하게 요약하는 전문가입니다. "
            "아래 대화 내용을 읽고 500자 이내로 요약하세요. "
            "요약은 '요약:'으로 시작하며 요약내용을 한국어로 알려주고, 발화자들의 흐름을 간결하게 압축하세요. "
            "대화를 이어나가지 말고, 반복하거나 자세히 재작성하지 마세요."
        )

        # 2. 대화 메시지 조립 (role 구분만 간단하게, 자연스러운 문장으로)
        dialogue_text = ""
        last_role = None

        for m in msgs:
            role = m.role.lower()
            prefix = "User" if role == "user" else "Assistant"
            if last_role != role:
                dialogue_text += f"\n{prefix}: {m.message.strip()}"
            else:
                dialogue_text += f" {m.message.strip()}"
            last_role = role

        # 3. 최종 프롬프트: Mixtral instruct 형식
        system_message = "당신은 한국어만 사용하는 AI 어시스턴트입니다. 모든 응답은 반드시 한국어로만 작성하세요."
        final_prompt = f"<s>[INST] <<SYS>>\n{system_message}\n<</SYS>>\n\n{instruction} [/INST]{dialogue_text.strip()}</s>"


        # 5. 요약 함수 호출 (string 입력으로 전달)
        raw_output = self.client.generate_summary(final_prompt)

        # 5-1. '요약: 사용자는'부터 추출하되, '요약:'은 제외하고 저장
        import re
        match = re.search(r"요약:\s*(사용자는.*?)(?=\n요약:|\Z)", raw_output, re.DOTALL)
        summary_text = match.group(1).strip() if match else raw_output.strip()

        # 6) DB에 요약 저장
        summary_repo.save(user_id, session_id, summary_text)
        print("✏️mixtral 요약완료 후 db에 저장완료")



        # 6-1) 요약 임베딩 + 벡터DB 저장
        from app.services.vector_db_service import VectorDBService
        yymmdd = session_id.split('_')[0]
        vector_db = VectorDBService()
        vector_db.add_document(
            summary_text,
            metadata={"session_id": session_id, "user_id": user_id, "date": yymmdd}
        )
        print( "🐥mixtral 요약후 임베딩성공 ")
        print(f"🐥 현재 벡터DB 문서 수: {len(vector_db.vectorstore.get()['documents'])}")




        # 7) DB 세션 닫기
        db.close()



     


