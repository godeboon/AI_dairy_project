def build_session_summary_prompt(user_chats: list) -> list:
    """세션 요약을 위한 프롬프트 구성"""
    system_content = """당신은 사용자의 대화 내용을 분석하여 요약과 키워드를 생성하는 전문가입니다.

요구사항:
1. 400자 내외로 대화 내용을 요약하세요 (나중에 이 요약본만 보고도 해당 대화의 맥락과 흐름을 파악할 수 있도록 작성)
2. 핵심 키워드 5개를 추출하세요
3. 추출한 키워드 5개를 바탕으로 육하원칙에 맞게 한 문장 또는 두 문장으로 핵심 문장을 작성하세요
4. JSON 형태로 응답하세요
5. 해당대화는 한사람과 나누는 대화임을 명심하세요.

응답 형식:
{
    "summary": "400자 내외 요약본",
    "key_sentence": 카워드 5개를 바탕으로 한 육하원칙의 문장 (1문장 혹은 2문장)",
    "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]
}"""

    user_content = f"다음 대화 내용을 요약해주세요.:\n\n" + "\n".join(user_chats)
    
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]

