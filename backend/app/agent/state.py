from typing import Any, List, Optional
from pydantic import BaseModel, Field


class AnswerRecord(BaseModel):
    question_index: int
    question_text: str
    worker_answer: str
    score: int
    missing_points: List[str] = Field(default_factory=list)
    is_followup: bool = False


class InterviewState(BaseModel):
    """Tracks state and progress during the candidate's scenario interview."""

    current_question_index: int = 0
    follow_up_count: int = 0
    active_question_text: Optional[str] = None
    answers: List[Any] = Field(default_factory=list)
    scores: List[int] = Field(default_factory=list)
    is_done: bool = False
