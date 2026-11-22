import json
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from app.agent.review import run_review_decision
from app.blueprints.loader import load_blueprint
from app.db import get_session
from app.models import Attempt, Worker
from app.schemas import APIError, APIResponse, AttemptCreate, AttemptResponse
from app.services.attempt_service import create_attempt

router = APIRouter(tags=["attempts"])


@router.post("/attempts", response_model=APIResponse[AttemptResponse])
def start_attempt(
    payload: AttemptCreate,
    request: Request,
    db: Session = Depends(get_session),
):
    # 1. Validate blueprint
    try:
        blueprint = load_blueprint(payload.skill_id)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="INVALID_SKILL",
                    message=f"Invalid skill_id '{payload.skill_id}'.",
                    hint=str(e),
                ),
            ).model_dump(),
        )

    # 2. Extract worker from Authorization Bearer token or fallback to first worker
    worker = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        worker = db.exec(select(Worker).where(Worker.token == token)).first()

    if not worker:
        # Fallback to first worker if no header or token match
        worker = db.exec(select(Worker)).first()

    if not worker:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="WORKER_NOT_FOUND",
                    message="No worker found. Please register worker first.",
                    hint="Call POST /api/workers first.",
                ),
            ).model_dump(),
        )

    # 3. Create attempt
    attempt = create_attempt(worker_id=worker.id, skill_id=blueprint.skill_id, db=db)

    # 4. Extract checklist from blueprint steps
    checklist = [
        {
            "id": s.id,
            "title": s.title,
            "critical": s.critical,
            "safety_critical": s.safety_critical,
        }
        for s in blueprint.steps
    ]

    return APIResponse[AttemptResponse](
        ok=True,
        data=AttemptResponse(
            attempt_id=attempt.id,
            challenge_code=attempt.challenge_code,
            checklist=checklist,
        ),
        error=None,
    )


@router.get("/attempts/{attempt_id}", response_model=APIResponse[dict])
def get_attempt_by_id(
    attempt_id: str,
    db: Session = Depends(get_session),
):
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

    # If the attempt is analyzing, trigger the AI analysis and review decision synchronously
    if attempt.status == "analyzing":
        review_result = run_review_decision(attempt=attempt, db=db)
        steps = review_result["steps"]
        fraud_flags = review_result["fraud_flags"]
        agent_log = review_result["agent_log"]
        decision = review_result["decision"]
        v_score = review_result["video_score"]
    else:
        steps = []
        if attempt.ai_result_json:
            try:
                ai_data = json.loads(attempt.ai_result_json)
                steps = ai_data.get("steps", [])
            except Exception:
                steps = []

        fraud_flags = []
        if attempt.fraud_flags_json:
            try:
                fraud_flags = json.loads(attempt.fraud_flags_json)
            except Exception:
                fraud_flags = []

        agent_log = [
            f"Status: {attempt.status}",
            f"Decision: {attempt.decision or 'pending'}",
        ]
        decision = attempt.decision
        v_score = attempt.video_score

    return APIResponse[dict](
        ok=True,
        data={
            "id": attempt.id,
            "worker_id": attempt.worker_id,
            "skill_id": attempt.skill_id,
            "status": attempt.status,
            "challenge_code": attempt.challenge_code,
            "interview_score": attempt.interview_score,
            "video_score": v_score,
            "decision": decision,
            "steps": steps,
            "fraud_flags": fraud_flags,
            "agent_log": agent_log,
        },
        error=None,
    )
