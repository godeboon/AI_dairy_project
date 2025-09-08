from typing import List, Dict

def build_weekly_vs_past_comparison_prompt(
    weekly_summaries: List[Dict], 
    past_sessions: Dict[str, List[Dict]], 
    query: str
) -> str:
    """
    일주일치 분석 vs 과거 유사 세션 비교 프롬프트
    
    Args:
        weekly_summaries: 일주일치 세션 요약 리스트 (시간순)
        past_sessions: 과거 유사 세션들 (yymmdd별 그룹화)
        query: 분석 주제
    """
    lines = []
    lines.append("당신은 사용자의 현재 일주일치 분석과 과거 유사한 세션들을 비교 분석하는 전문가입니다.")
    lines.append(f"분석 주제: {query}")
    lines.append("")
    
    # 일주일치 분석 내용을 날짜별로 그룹화
    lines.append("=== 현재 일주일치 대화 분석 (시간순) ===")
    
    # 날짜별로 그룹화
    date_groups = {}
    for summary in weekly_summaries:
        yymmdd = summary['yymmdd']
        if yymmdd not in date_groups:
            date_groups[yymmdd] = []
        date_groups[yymmdd].append(summary)
    
    # 날짜 순서대로 정렬하여 출력
    for yymmdd in sorted(date_groups.keys()):
        lines.append(f"--- {yymmdd} ---")
        for summary in date_groups[yymmdd]:
            lines.append(f"[{summary['session_id']}] {summary['summary']}")
        lines.append("")
    
    # 과거 유사 세션들
    lines.append("=== 과거 유사한 세션들 ===")
    y_keys = sorted(past_sessions.keys())
    for y in y_keys:
        lines.append(f"--- {y} ---")
        for item in past_sessions[y]:
            sid = item["sid"]
            lines.append(f"[{sid}]")
            for msg in item["chats"]:
                lines.append(msg)
            lines.append("")
    
    lines.append("분석 요청:")
    lines.append("다음 3가지 관점에서 JSON 형태로 응답해주세요:")
    lines.append("")
    lines.append("1) 유사한 패턴: 현재 일주일치와 과거 세션들에서 관찰되는 반복되는 패턴이나 행동 양식")
    lines.append("2) 성향: 사용자의 일관된 성격적 특성이나 대화 스타일")
    lines.append("3) 무의식적 통찰: 사용자가 의식하지 못하는 심리적 패턴이나 내재된 욕구")
    lines.append("")
    lines.append("응답 형식:")
    lines.append('{')
    lines.append('    "유사한 패턴": "관찰된 패턴 설명 (없으면 \'없음\')",')
    lines.append('    "성향": "관찰된 성향 설명 (없으면 \'없음\')",')
    lines.append('    "무의식적 통찰": "관찰된 통찰 설명 (없으면 \'없음\')"')
    lines.append('}')
    lines.append("")
    lines.append("주의사항:")
    lines.append("- 과거 세션들끼리의 비교는 하지 마세요")
    lines.append("- 현재 일주일치 vs 과거 유사 세션들의 비교에 집중하세요")
    lines.append(f"- 주제 \"{query}\"에 대한 분석에 집중하세요")
    lines.append("- 특별히 관찰되는 패턴/성향/통찰이 없다면 '없음'으로 기록하세요")
    
    return "\n".join(lines)


