import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Worker(SQLModel, table=True):
    __tablename__ = "workers"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    language: str
    area: str
    phone_optional: Optional[str] = None
    device_fp: Optional[str] = None
    token: str
    consent_at: datetime = Field(default_factory=utc_now)
    created_at: datetime = Field(default_factory=utc_now)


class Attempt(SQLModel, table=True):
    __tablename__ = "attempts"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    worker_id: str = Field(foreign_key="workers.id")
    skill_id: str
    status: str = Field(default="created")
    challenge_code: str
    interview_json: Optional[str] = None
    interview_score: Optional[float] = None
    video_path: Optional[str] = None
    video_sha256: Optional[str] = None
    video_phash: Optional[str] = None
    video_meta_json: Optional[str] = None
    ai_result_json: Optional[str] = None
    fraud_flags_json: Optional[str] = None
    video_score: Optional[float] = None
    decision: Optional[str] = None
    coaching_json: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class WitnessInvite(SQLModel, table=True):
    __tablename__ = "witness_invites"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    attempt_id: str = Field(foreign_key="attempts.id")
    token: str
    created_at: datetime = Field(default_factory=utc_now)
    used_at: Optional[datetime] = None


class Vouch(SQLModel, table=True):
    __tablename__ = "vouches"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    invite_id: str = Field(foreign_key="witness_invites.id")
    attempt_id: str = Field(foreign_key="attempts.id")
    witness_name: str
    role: str
    device_fp: Optional[str] = None
    seen_in_person: bool = Field(default=True)
    known_years_bucket: str
    would_hire: bool = Field(default=True)
    verdict: str  # yes | needs_work
    weight: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=utc_now)


class Credential(SQLModel, table=True):
    __tablename__ = "credentials"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    attempt_id: str = Field(foreign_key="attempts.id")
    worker_id: str = Field(foreign_key="workers.id")
    skill_id: str
    tier: int
    trust_score: float
    payload_json: str
    signature_b64: str
    evidence_sha256: str
    issued_at: datetime = Field(default_factory=utc_now)
    revoked: bool = Field(default=False)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    ts: datetime = Field(default_factory=utc_now)
    actor: str
    action: str
    ref_id: Optional[str] = None
    detail_json: Optional[str] = None
