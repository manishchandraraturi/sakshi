from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIError(BaseModel):
    code: str
    message: str
    hint: Optional[str] = None


class APIResponse(BaseModel, Generic[T]):
    ok: bool
    data: Optional[T] = None
    error: Optional[APIError] = None


class WorkerCreate(BaseModel):
    name: str
    language: str
    area: str
    consent: bool
    device_fp: str
    phone_optional: Optional[str] = None


class WorkerResponse(BaseModel):
    worker_id: str
    token: str


class AttemptCreate(BaseModel):
    skill_id: str


class AttemptResponse(BaseModel):
    attempt_id: str
    challenge_code: str
    checklist: List[Any]


class SkillStepSummary(BaseModel):
    id: str
    title: str
    critical: bool


class SkillSummary(BaseModel):
    id: str
    skill_id: str
    name: str
    steps: List[SkillStepSummary]


class TradeSummary(BaseModel):
    trade: str
    skills: List[SkillSummary]


class InterviewRequest(BaseModel):
    answer: Optional[str] = None


class InterviewResponse(BaseModel):
    question: Optional[str] = None
    done: bool
    progress: dict[str, Any]
