"""
backend/app/services/witness_service.py

Service layer for generating witness invite links, retrieving witness review
page data, and processing submitted vouches with anti-fraud/weight calculations.
"""
import secrets
from typing import Any, List, Optional
from sqlalchemy import func
from sqlmodel import Session, select

from app.blueprints.loader import load_blueprint
from app.models import Attempt, Credential, Vouch, WitnessInvite, Worker, utc_now
from app.schemas import VouchCreate
from app.trust.weights import calculate_weight


def create_witness_invites(
    attempt_id: str,
    count: int,
    db: Session,
    base_url: str,
) -> List[dict[str, str]]:
    """
    Creates `count` one-time witness invite tokens for an attempt and transitions
    the attempt status to 'awaiting_witnesses'.
    """
    attempt = db.exec(select(Attempt).where(Attempt.id == attempt_id)).first()
    if not attempt:
        raise ValueError(f"Attempt '{attempt_id}' not found.")

    valid_transition_statuses = (
        "created",
        "interviewing",
        "awaiting_video",
        "analyzing",
        "reviewed",
        "awaiting_witnesses",
    )
    if attempt.status in valid_transition_statuses:
        attempt.status = "awaiting_witnesses"
        attempt.updated_at = utc_now()
        db.add(attempt)

    invites: List[dict[str, str]] = []
    base_clean = base_url.rstrip("/")

    for _ in range(max(1, count)):
        token = secrets.token_urlsafe(16)
        invite = WitnessInvite(attempt_id=attempt_id, token=token)
        db.add(invite)
        invites.append({
            "token": token,
            "url": f"{base_clean}/w/{token}",
        })

    db.commit()
    return invites


def get_witness_page_data(token: str, db: Session) -> dict[str, Any]:
    """
    Retrieves public minimal review data for a witness: worker's first name,
    skill name, step checklist, and video clip URL.
    Enforces that the token exists and has not already been used.
    """
    invite = db.exec(
        select(WitnessInvite).where(WitnessInvite.token == token)
    ).first()
    if not invite:
        raise ValueError("INVITE_NOT_FOUND")

    if invite.used_at is not None:
        raise ValueError("INVITE_ALREADY_USED")

    attempt = db.exec(select(Attempt).where(Attempt.id == invite.attempt_id)).first()
    if not attempt:
        raise ValueError("ATTEMPT_NOT_FOUND")

    worker = db.exec(select(Worker).where(Worker.id == attempt.worker_id)).first()
    worker_first_name = worker.name.strip().split()[0] if (worker and worker.name) else "Worker"

    try:
        bp = load_blueprint(attempt.skill_id)
        skill_name = bp.name
        steps = [{"id": s.id, "title": s.title} for s in bp.steps]
    except Exception:
        skill_name = attempt.skill_id
        steps = []

    clip_url: Optional[str] = None
    if attempt.video_path:
        clip_url = f"/api/media/clips/{attempt.id}.mp4"

    return {
        "worker_first_name": worker_first_name,
        "skill": skill_name,
        "skill_name": skill_name,
        "clip_url": clip_url,
        "steps": steps,
    }


def submit_vouch(
    token: str,
    vouch_data: VouchCreate,
    db: Session,
) -> Vouch:
    """
    Validates the invite token, checks fraud criteria (reciprocity, same device,
    duplicate device fingerprint, credentials), calculates weight via pure engine,
    and commits the Vouch and marks the invite as used.
    """
    invite = db.exec(
        select(WitnessInvite).where(WitnessInvite.token == token)
    ).first()
    if not invite:
        raise ValueError("INVITE_NOT_FOUND")

    if invite.used_at is not None:
        raise ValueError("INVITE_ALREADY_USED")

    attempt = db.exec(select(Attempt).where(Attempt.id == invite.attempt_id)).first()
    if not attempt:
        raise ValueError("ATTEMPT_NOT_FOUND")

    worker = db.exec(select(Worker).where(Worker.id == attempt.worker_id)).first()

    witness_name = (vouch_data.witness_name or vouch_data.name or "Anonymous").strip()
    known_years_bucket = (
        vouch_data.known_years_bucket or vouch_data.known_years or "1-3"
    ).strip()
    device_fp = (vouch_data.device_fp or "").strip()

    # 1. Check same device as worker
    if vouch_data.same_device_as_worker is not None:
        same_device = vouch_data.same_device_as_worker
    else:
        same_device = bool(
            device_fp and worker and worker.device_fp and device_fp == worker.device_fp
        )

    # 2. Check if witness holds own credential
    if vouch_data.has_credential is not None:
        has_cred = vouch_data.has_credential
    else:
        matching_worker = db.exec(
            select(Worker).where(func.lower(Worker.name) == witness_name.lower())
        ).first()
        if not matching_worker and device_fp:
            matching_worker = db.exec(
                select(Worker).where(Worker.device_fp == device_fp)
            ).first()

        if matching_worker:
            cred = db.exec(
                select(Credential).where(
                    Credential.worker_id == matching_worker.id,
                    Credential.revoked == False,
                )
            ).first()
            has_cred = bool(cred)
        else:
            has_cred = False

    # 3. Check reciprocity: has the candidate worker previously vouched for this witness?
    if vouch_data.is_reciprocal is not None:
        is_recip = vouch_data.is_reciprocal
    else:
        matching_worker = db.exec(
            select(Worker).where(func.lower(Worker.name) == witness_name.lower())
        ).first()
        if matching_worker and worker:
            recip_vouch = db.exec(
                select(Vouch)
                .join(Attempt, Vouch.attempt_id == Attempt.id)
                .where(
                    Attempt.worker_id == matching_worker.id,
                    func.lower(Vouch.witness_name) == worker.name.lower(),
                )
            ).first()
            is_recip = bool(recip_vouch)
        else:
            is_recip = False

    # 4. Check duplicate device fingerprint among existing vouches for this attempt
    existing_vouches = db.exec(
        select(Vouch).where(Vouch.attempt_id == attempt.id)
    ).all()
    existing_fps = [v.device_fp for v in existing_vouches if v.device_fp]

    # 5. Deterministic weight calculation
    weight = calculate_weight(
        role=vouch_data.role,
        has_credential=has_cred,
        is_reciprocal=is_recip,
        seen_in_person=vouch_data.seen_in_person,
        same_device_as_worker=same_device,
        device_fp=device_fp,
        existing_vouch_device_fps=existing_fps,
        verdict=vouch_data.verdict,
    )

    # 6. Save vouch and consume invite
    vouch = Vouch(
        invite_id=invite.id,
        attempt_id=attempt.id,
        witness_name=witness_name,
        role=vouch_data.role,
        device_fp=device_fp or None,
        seen_in_person=vouch_data.seen_in_person,
        known_years_bucket=known_years_bucket,
        would_hire=vouch_data.would_hire,
        verdict=vouch_data.verdict,
        weight=weight,
    )
    db.add(vouch)
    invite.used_at = utc_now()
    db.add(invite)
    db.commit()
    db.refresh(vouch)

    return vouch
