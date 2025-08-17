# 감정 변화 분석 프롬프트
emotion_trend_prompt = """
다음 7일간의 감정 데이터를 분석해서 감정 변화 패턴을 JSON 형태로 응답해주세요:

7일간 감정 데이터:
{weekly_emotions}

7일간 감정 점수:
{weekly_scores}

응답 형식:
{{
    "trend": "감정 변화 트렌드",
    "dominant_emotion": "가장 지배적인 감정",
    "emotion_stability": "감정 안정성 점수 (0.0~1.0)",
    "key_changes": ["주요 변화점1", "주요 변화점2"],
    "recommendation": "감정 관리 조언"
}}

주의사항:
- 감정 변화의 전체적인 패턴을 분석
- 가장 두드러진 변화점들을 찾아내기
- 구체적이고 실용적인 조언 제공
"""

# 키워드 패턴 분석 프롬프트
keyword_pattern_prompt = """
다음 7일간의 키워드 데이터를 분석해서 키워드 패턴을 JSON 형태로 응답해주세요:

7일간 키워드 데이터:
{weekly_keywords}

응답 형식:
{{
    "main_themes": ["주요 테마1", "주요 테마2", "주요 테마3"],
    "trending_keywords": ["트렌딩 키워드1", "트렌딩 키워드2"],
    "recurring_patterns": ["반복되는 패턴1", "반복되는 패턴2"],
    "insights": "키워드 분석을 통한 인사이트"
}}

주의사항:
- 가장 자주 등장하는 키워드와 테마 파악
- 시간에 따른 키워드 변화 패턴 분석
- 삶의 다양한 측면별로 키워드분석하여 최종 인사이트 제공
"""

# 종합 분석 프롬프트
comprehensive_analysis_prompt = """
감정 분석과 키워드 분석 결과를 종합해서 최종 주간 분석을 JSON 형태로 응답해주세요:

감정 분석 결과:
{emotion_analysis}

키워드 분석 결과:
{keyword_analysis}

7일간 요약:
{weekly_summaries}

응답 형식:
{{
    "overall_mood": "전체적인 기분 상태",
    "life_satisfaction": "삶의 만족도 점수 (0.0~1.0)",
    "stress_level": "스트레스 수준 (0.0~1.0)",
    "social_activity": "사회적 활동 수준 (0.0~1.0)",
    "key_achievements": ["주요 성취1", "주요 성취2"],
    "challenges": ["도전 과제1", "도전 과제2"],
    "growth_areas": ["성장 영역1", "성장 영역2"],
    "weekly_theme": "이번 주의 주요 테마",
    "next_week_focus": "다음 주 집중할 점",
    "overall_assessment": "전체적인 주간 평가"
}}

주의사항:
- 감정과 키워드를 종합한 통합적 분석
- 구체적이고 실용적인 인사이트 제공
- 다음 주를 위한 제안 포함
""" 