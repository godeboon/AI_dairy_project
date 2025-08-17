class DiaryPromptService:
    def generate_diary_prompt(self, today_chats: list) -> str:
        """일기 생성 프롬프트"""
        prompt = f"""
        오늘의 대화를 바탕으로 일기를 작성해주세요.
        
        대화 내용:
        {today_chats}
        
        요구사항:
        1. 대화의 흐름을 자연스럽게 일기 형태로 작성
        2. 사용자의 감정과 생각을 반영
        3. 500자 이내로 작성
        4. 한국어로 작성
        5. 날짜적지말기
        """
        return prompt 