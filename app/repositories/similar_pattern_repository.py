from sqlalchemy.orm import Session
from app.models.db.study_model import SimilarPattern
import json
from typing import List, Dict, Optional

class SimilarPatternRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_user_and_sessions(self, user_id: int, session_ids: List[str]) -> Optional[SimilarPattern]:
        """사용자와 유사 세션들로 기존 패턴 찾기"""
        print(f"🔍 [DEBUG] find_by_user_and_sessions 시작: user_id={user_id}, session_ids={session_ids}")
        
        patterns = self.db.query(SimilarPattern).filter(
            SimilarPattern.user_id == user_id
        ).all()
        
        print(f"🔍 [DEBUG] 사용자 {user_id}의 기존 패턴 수: {len(patterns)}")
        
        for i, pattern in enumerate(patterns):
            print(f"🔍 [DEBUG] 패턴 {i+1} 분석 시작: pattern.id={pattern.id}")
            
            # 기존 패턴의 모든 세션들을 중복 제거된 고유 세션들로 변환
            existing_sessions = set()
            for j, session_group in enumerate(pattern.similar_session_ids):
                print(f"🔍 [DEBUG] 패턴 {i+1}의 세션 그룹 {j+1}: {session_group}")
                existing_sessions.update(session_group)
            
            print(f"🔍 [DEBUG] 패턴 {i+1}의 중복 제거된 기존 세션들: {existing_sessions}")
            print(f"🔍 [DEBUG] 새로운 세션들: {session_ids}")
            
            # 새로운 세션들이 기존 패턴의 모든 세션을 포함하는지 확인
            new_set = set(session_ids)
            
            print(f"🔍 [DEBUG] 기존 세션 집합: {existing_sessions}")
            print(f"🔍 [DEBUG] 새로운 세션 집합: {new_set}")
            print(f"🔍 [DEBUG] 기존 세션이 새로운 세션에 포함되는가? {existing_sessions.issubset(new_set)}")
            
            if existing_sessions.issubset(new_set):
                print(f"🔍 [DEBUG] 매칭되는 패턴 발견: pattern.id={pattern.id}")
                return pattern
            else:
                print(f"🔍 [DEBUG] 패턴 {i+1}은 매칭되지 않음")
        
        print(f"🔍 [DEBUG] 매칭되는 패턴이 없음")
        return None
    
    def save_new_pattern(self, user_id: int, analysis_id: int, query: str, 
                        similar_sessions: List[str], insights: Dict[str, str]):
        """새로운 패턴 저장"""
        print(f"🆕 [DEBUG] save_new_pattern 시작: user_id={user_id}, analysis_id={analysis_id}")
        try:
            new_pattern = SimilarPattern(
                user_id=user_id,
                analysis_ids=[analysis_id],
                queries=[query],
                similar_session_ids=[similar_sessions],
                pattern_insights=[insights]
            )
            print(f"🆕 [DEBUG] SimilarPattern 객체 생성 완료")
            
            self.db.add(new_pattern)
            print(f"🆕 [DEBUG] DB에 add 완료")
            
            self.db.commit()
            print(f"🆕 [DEBUG] DB commit 완료")
            
            print(f"🆕 새로운 패턴 생성: analysis_id={analysis_id}, 세션 {len(similar_sessions)}개")
        except Exception as e:
            print(f"❌ [ERROR] save_new_pattern 실패: {e}")
            self.db.rollback()
            raise
    
    def update_existing_pattern(self, pattern: SimilarPattern, analysis_id: int, 
                               query: str, similar_sessions: List[str], 
                               insights: Dict[str, str]):
        """기존 패턴 업데이트"""
        print(f"✅ [DEBUG] update_existing_pattern 시작: pattern.id={pattern.id}, analysis_id={analysis_id}")
        
        # 새로운 analysis_id가 기존에 없으면 항상 저장
        # if analysis_id not in pattern.analysis_ids:  # 개발용으로 주석처리
        print(f"✅ [DEBUG] 새로운 analysis_id 추가: {analysis_id}")
        
        # 1. analysis_ids - 단순 리스트 확장
        pattern.analysis_ids = pattern.analysis_ids + [analysis_id]
        
        # 2. queries - 단순 리스트 확장
        pattern.queries = pattern.queries + [query]
        
        # 3. similar_session_ids - 새로운 세션 그룹 전체 추가 (중복 허용)
        pattern.similar_session_ids = pattern.similar_session_ids + [similar_sessions]
        print(f"✅ [DEBUG] 새로운 세션 그룹 추가: {similar_sessions}")
        
        # 4. pattern_insights - 2차원 리스트 확장
        pattern.pattern_insights = pattern.pattern_insights + [insights]
        
        print(f"✅ [DEBUG] 패턴 데이터 업데이트 완료")
        
        self.db.commit()
        print(f"✅ [DEBUG] DB commit 완료")
        
        print(f"✅ 패턴 확장: analysis_id={analysis_id}, 세션 {len(similar_sessions)}개")
        # else:
        #     print(f"⚠️ [DEBUG] analysis_id {analysis_id}가 이미 존재함. 업데이트 스킵")
    
    def save_or_update_pattern(self, user_id: int, analysis_id: int, query: str,
                              similar_sessions: List[str], insights: Dict[str, str]):
        """패턴 저장 또는 업데이트 (통합 메서드)"""
        existing_pattern = self.find_by_user_and_sessions(user_id, similar_sessions)
        
        if existing_pattern:
            self.update_existing_pattern(existing_pattern, analysis_id, query, 
                                       similar_sessions, insights)
        else:
            self.save_new_pattern(user_id, analysis_id, query, 
                                similar_sessions, insights)
    
    def get_by_id(self, similar_pattern_id: int) -> Optional[SimilarPattern]:
        """ID로 SimilarPattern 조회"""
        try:
            pattern = self.db.query(SimilarPattern).filter(
                SimilarPattern.id == similar_pattern_id
            ).first()
            return pattern
        except Exception as e:
            print(f"❌ [ERROR] get_by_id 실패: {e}")
            return None
    
    def get_by_id_and_user_id(self, similar_pattern_id: int, user_id: int) -> Optional[SimilarPattern]:
        """ID와 user_id로 SimilarPattern 조회 (더 안전한 조회)"""
        try:
            pattern = self.db.query(SimilarPattern).filter(
                SimilarPattern.id == similar_pattern_id,
                SimilarPattern.user_id == user_id
            ).first()
            return pattern
        except Exception as e:
            print(f"❌ [ERROR] get_by_id_and_user_id 실패: {e}")
            return None
    
    def get_by_user_id_and_not_used(self, user_id: int) -> Optional[SimilarPattern]:
        """user_id로 SimilarPattern 조회 (마킹되지 않은 것만)"""
        try:
            pattern = self.db.query(SimilarPattern).filter(
                SimilarPattern.user_id == user_id,
                SimilarPattern.is_used_in_personality_analysis == False
            ).first()
            return pattern
        except Exception as e:
            print(f"❌ [ERROR] get_by_user_id_and_not_used 실패: {e}")
            return None


