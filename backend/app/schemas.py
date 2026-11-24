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


class WitnessInviteCreate(BaseModel):
    count: int = 3


class WitnessInviteResponse(BaseModel):
    token: str
    url: str


class WitnessPageData(BaseModel):
    worker_first_name: str
    skill: str
    skill_name: Optional[str] = None
    clip_url: Optional[str] = None
    steps: List[dict[str, Any]] = []


class VouchCreate(BaseModel):
    witness_name: Optional[str] = None
    name: Optional[str] = None
    role: str = "peer"
    institute_code: Optional[str] = None
    seen_in_person: bool = True
    known_years_bucket: Optional[str] = None
    known_years: Optional[str] = None
    would_hire: bool = True
    verdict: str = "yes"
    device_fp: Optional[str] = None
    has_credential: Optional[bool] = None
    is_reciprocal: Optional[bool] = None
    same_device_as_worker: Optional[bool] = None


class VouchResponse(BaseModel):
    vouch_id: str
    weight: float
    attempt_id: str
    status: str = "recorded"


class CredentialResponse(BaseModel):
    credential_id: str
    tier: int
    trust_score: float
    payload: dict[str, Any]
    signature: str
    issued_at: Optional[str] = None
    valid_until: Optional[str] = None


class PubkeyResponse(BaseModel):
    pubkey: str


class DirectoryItem(BaseModel):
    credential_id: str
    name: str
    trade: str
    skill: str
    tier: int
    trust_score: float
    area: str
    issued_at: Optional[str] = None


class RerecordResponse(BaseModel):
    attempt_id: str
    status: str
    video_score: float
    decision: str
    steps: List[dict[str, Any]] = []
    agent_log: List[str] = []
    rerecorded_steps: List[str] = []


class AnalyticsResponse(BaseModel):
    total_workers: int
    tier_distribution: dict[str, int]
    trade_distribution: dict[str, int]
    total_vouches: int




