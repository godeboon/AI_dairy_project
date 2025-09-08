from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.connection import get_db
from app.models.db.study_model import PersonalityReport
from typing import Dict, Any

router = APIRouter()

@router.get("/personality-report/{report_id}")
async def get_personality_report(
    report_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    personality_reports 테이블에서 report_id로 데이터를 조회하고 파싱해서 전달
    """
    print(f"🔍 [constellation.py] personality-report 요청 받음: report_id={report_id}")
    
    try:
        # 1. report_id로 PersonalityReport 조회
        print(f"📊 [constellation.py] DB에서 PersonalityReport 조회 시작")
        personality_report = db.query(PersonalityReport).filter(
            PersonalityReport.id == report_id
        ).first()
        
        if not personality_report:
            print(f"❌ [constellation.py] PersonalityReport를 찾을 수 없음: report_id={report_id}")
            raise HTTPException(status_code=404, detail="Personality report not found")
        
        print(f"✅ [constellation.py] PersonalityReport 조회 성공: user_id={personality_report.user_id}")
        
        # 2. 데이터 파싱
        query = personality_report.query
        report_result = personality_report.report_result
        
        print(f"📝 [constellation.py] 원본 데이터:")
        print(f"   - query: {query}")
        print(f"   - report_result keys: {list(report_result.keys()) if isinstance(report_result, dict) else 'Not a dict'}")
        
        # 3. report_result에서 각 섹션 추출
        emotional_pattern = report_result.get('정서적 패턴', '')
        personality_tendency = report_result.get('성향', '')
        unconscious_insight = report_result.get('무의식적 통찰', '')
        
        print(f"🎯 [constellation.py] 파싱된 섹션들:")
        print(f"   - 정서적 패턴 길이: {len(emotional_pattern)}")
        print(f"   - 성향 길이: {len(personality_tendency)}")
        print(f"   - 무의식적 통찰 길이: {len(unconscious_insight)}")
        
        # 4. 파싱된 데이터 반환
        parsed_data = {
            'query': query,
            'emotional_pattern': emotional_pattern,
            'personality_tendency': personality_tendency,
            'unconscious_insight': unconscious_insight,
            'user_id': personality_report.user_id,
            'timestamp': personality_report.timestamp,
            'date_str': personality_report.date_str
        }
        
        print(f"✅ [constellation.py] 파싱 완료, 데이터 반환 준비")
        return parsed_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
