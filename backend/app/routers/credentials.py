"""
backend/app/routers/credentials.py

Router for issuing, finalizing, signing, and fetching Ed25519 digital credentials.
"""
import json
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.blueprints.loader import load_blueprint
from app.config import settings
from app.crypto.card import generate_share_card
from app.crypto.pdf import generate_pdf
from app.crypto.sign import get_public_key_b64, sign_payload
from app.db import get_session
from app.models import Attempt, Credential, Vouch, Worker, utc_now
from app.schemas import APIError, APIResponse, CredentialResponse, PubkeyResponse
from app.trust.score import check_safety_gate
from app.trust.tiers import calculate_tier, calculate_trust_score

router = APIRouter(tags=["credentials"])


@router.post(
    "/attempts/{attempt_id}/finalize",
    response_model=APIResponse[CredentialResponse],
)
def finalize_attempt_and_issue_credential(
    attempt_id: str,
    db: Session = Depends(get_session),
):
    """
    Finalizes a candidate's attempt:
    1. Aggregates witness vouches (weights, counts, roles).
    2. Runs deterministic tier and trust score engines.
    3. Builds canonical signed Ed25519 credential payload.
    4. Persists Credential, sets attempt status='finalized'.
    5. Returns credential response (idempotent).
    """
    attempt = db.exec(select(Attempt).where(Attempt.id == attempt_id)).first()
    if not attempt:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="ATTEMPT_NOT_FOUND",
                    message=f"Attempt '{attempt_id}' not found.",
                ),
            ).model_dump(),
        )

    # Idempotency check: if already finalized, return existing credential
    existing_cred = db.exec(
        select(Credential).where(Credential.attempt_id == attempt_id)
    ).first()
    if existing_cred:
        try:
            payload_data = json.loads(existing_cred.payload_json)
        except Exception:
            payload_data = {}

        return APIResponse[CredentialResponse](
            ok=True,
            data=CredentialResponse(
                credential_id=existing_cred.id,
                tier=existing_cred.tier,
                trust_score=existing_cred.trust_score,
                payload=payload_data,
                signature=existing_cred.signature_b64,
                issued_at=existing_cred.issued_at.isoformat(),
                valid_until=payload_data.get("valid_until"),
            ),
            error=None,
        )

    # 1. Fetch vouches and aggregate weights
    vouches = db.exec(select(Vouch).where(Vouch.attempt_id == attempt_id)).all()
    total_weight = sum(v.weight for v in vouches)
    distinct_witnesses = len(
        set(v.witness_name.lower().strip() for v in vouches if v.witness_name)
    )
    has_trainer_or_employer = any(
        v.role.lower().strip() in ("trainer", "employer") and v.weight > 0
        for v in vouches
    )

    # 2. Extract attempt evaluation metrics
    video_score_val = attempt.video_score if attempt.video_score is not None else 0.0
    interview_score_val = (
        attempt.interview_score if attempt.interview_score is not None else 0.0
    )

    fraud_flags = (
        json.loads(attempt.fraud_flags_json) if attempt.fraud_flags_json else []
    )
    has_fraud_flag = len(fraud_flags) > 0

    evaluated_steps: list[dict[str, Any]] = []
    if attempt.ai_result_json:
        try:
            parsed_ai = json.loads(attempt.ai_result_json)
            evaluated_steps = parsed_ai.get("steps", [])
        except Exception:
            evaluated_steps = []

    # 3. Check safety gate and critical steps via blueprint
    try:
        blueprint = load_blueprint(attempt.skill_id)
        safety_passed, _ = check_safety_gate(evaluated_steps, blueprint.steps)
        failed_critical = [
            s["id"]
            for s in evaluated_steps
            if s.get("critical") and s.get("verdict") in ("fail", "unclear")
        ]
        critical_steps_pass = len(failed_critical) == 0
        safety_gate_failed = not safety_passed
        trade = blueprint.trade
        skill_name = blueprint.name
    except Exception:
        safety_gate_failed = False
        critical_steps_pass = True
        trade = "Vocational"
        skill_name = attempt.skill_id

    # 4. Deterministic Tier & Trust Score calculation
    computed_tier = calculate_tier(
        video_score=video_score_val,
        critical_steps_pass=critical_steps_pass,
        has_fraud_flag=has_fraud_flag,
        safety_gate_failed=safety_gate_failed,
        witness_weight=total_weight,
        distinct_witnesses=distinct_witnesses,
        has_trainer_or_employer=has_trainer_or_employer,
    )
    computed_trust_score = float(
        calculate_trust_score(
            video_score=video_score_val,
            interview_score=interview_score_val,
            total_weight=total_weight,
        )
    )

    # 5. Worker details
    worker = db.exec(select(Worker).where(Worker.id == attempt.worker_id)).first()
    worker_name = worker.name if worker else "Worker"
    area = worker.area if worker else "Unknown"

    # 6. Build canonical payload & Ed25519 signature
    cred_id = str(uuid.uuid4())
    issued_at = utc_now()
    valid_until = (issued_at + timedelta(days=365)).isoformat()
    payload: Dict[str, Any] = {
        "cred_id": cred_id,
        "worker_name": worker_name,
        "area": area,
        "trade": trade,
        "skill": skill_name,
        "tier": computed_tier,
        "trust_score": int(computed_trust_score),
        "issued_at": issued_at.isoformat(),
        "valid_until": valid_until,
        "evidence_sha256": attempt.video_sha256 or "none",
        "witness_count": len(vouches),
    }

    signature_b64, pubkey_b64 = sign_payload(payload)

    # 7. Persist Credential & update Attempt status
    credential = Credential(
        id=cred_id,
        attempt_id=attempt.id,
        worker_id=attempt.worker_id,
        skill_id=attempt.skill_id,
        tier=computed_tier,
        trust_score=computed_trust_score,
        payload_json=json.dumps(payload, sort_keys=True, separators=(",", ":")),
        signature_b64=signature_b64,
        evidence_sha256=attempt.video_sha256 or "none",
        issued_at=issued_at,
        revoked=False,
    )
    db.add(credential)

    attempt.status = "finalized"
    attempt.updated_at = utc_now()
    db.add(attempt)
    db.commit()
    db.refresh(credential)

    return APIResponse[CredentialResponse](
        ok=True,
        data=CredentialResponse(
            credential_id=credential.id,
            tier=credential.tier,
            trust_score=credential.trust_score,
            payload=payload,
            signature=signature_b64,
            issued_at=issued_at.isoformat(),
            valid_until=valid_until,
        ),
        error=None,
    )


@router.get(
    "/credentials/{credential_id}/card.png",
    response_class=Response,
)
def get_credential_card(
    credential_id: str,
    db: Session = Depends(get_session),
):
    """
    Renders and returns a 600x1000 WhatsApp share-card PNG with QR code.
    """
    cred = db.exec(
        select(Credential).where(Credential.id == credential_id)
    ).first()
    if not cred:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="CREDENTIAL_NOT_FOUND",
                    message=f"Credential '{credential_id}' not found.",
                ),
            ).model_dump(),
        )

    try:
        payload_data = json.loads(cred.payload_json)
    except Exception:
        payload_data = {
            "cred_id": cred.id,
            "worker_name": "Tradesperson",
            "tier": cred.tier,
            "trust_score": cred.trust_score,
        }

    verify_url = f"{settings.PUBLIC_BASE_URL}/c/{cred.id}"
    card_bytes = generate_share_card(payload_data, verify_url)

    return Response(
        content=card_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="sakshi_{cred.id[:8]}.png"',
        },
    )


@router.get(
    "/credentials/{credential_id}/pdf",
    response_class=Response,
)
def get_credential_pdf(
    credential_id: str,
    db: Session = Depends(get_session),
):
    """
    Renders and returns a high-resolution A4 certificate PDF with Ed25519 verification QR code.
    """
    cred = db.exec(
        select(Credential).where(Credential.id == credential_id)
    ).first()
    if not cred:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="CREDENTIAL_NOT_FOUND",
                    message=f"Credential '{credential_id}' not found.",
                ),
            ).model_dump(),
        )

    try:
        payload_data = json.loads(cred.payload_json)
    except Exception:
        payload_data = {
            "cred_id": cred.id,
            "worker_name": "Tradesperson",
            "tier": cred.tier,
            "trust_score": cred.trust_score,
        }

    verify_url = f"{settings.PUBLIC_BASE_URL}/c/{cred.id}"
    pdf_bytes = generate_pdf(payload_data, verify_url)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="credential_{cred.id}.pdf"',
        },
    )


@router.get(
    "/credentials/{credential_id}",
    response_model=APIResponse[dict],
)
def get_credential(
    credential_id: str,
    db: Session = Depends(get_session),
):
    """
    Retrieve public digital credential with payload, signature, and verification key.
    """
    cred = db.exec(
        select(Credential).where(Credential.id == credential_id)
    ).first()
    if not cred:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="CREDENTIAL_NOT_FOUND",
                    message=f"Credential '{credential_id}' not found.",
                ),
            ).model_dump(),
        )

    try:
        payload_data = json.loads(cred.payload_json)
    except Exception:
        payload_data = {}

    return APIResponse[dict](
        ok=True,
        data={
            "credential_id": cred.id,
            "attempt_id": cred.attempt_id,
            "worker_id": cred.worker_id,
            "skill_id": cred.skill_id,
            "tier": cred.tier,
            "trust_score": cred.trust_score,
            "payload": payload_data,
            "signature": cred.signature_b64,
            "pubkey": get_public_key_b64(),
            "issued_at": cred.issued_at.isoformat(),
            "revoked": cred.revoked,
        },
        error=None,
    )


@router.get(
    "/pubkey",
    response_model=APIResponse[PubkeyResponse],
)
def get_public_key():
    """
    Returns server Ed25519 public key in base64 format.
    """
    return APIResponse[PubkeyResponse](
        ok=True,
        data=PubkeyResponse(pubkey=get_public_key_b64()),
        error=None,
    )
