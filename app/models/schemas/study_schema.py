from pydantic import BaseModel
from typing import Optional

class DiaryResponse(BaseModel):
    diary_id: int
    content: str

class DiarySevenResponse(BaseModel):
    report_id: int
    emotions: list
    scores: list
    keywords: list
    summary: str

class EncouragementResponse(BaseModel):
    encouragement_id: int
    content: str 