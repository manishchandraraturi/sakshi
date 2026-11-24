import json
from pathlib import Path
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from app.agent.loop import get_default_ai
from app.agent.prompts import ANALYZER_SYSTEM_PROMPT, build_analyzer_user_prompt
from app.agent.review import run_review_decision
from app.ai.utils import AnalyzerResult, validate_json
from app.blueprints.loader import load_blueprint
from app.db import get_session
from app.models import Attempt, Worker, utc_now
from app.schemas import APIError, APIResponse, AttemptCreate, AttemptResponse
from app.services.attempt_service import create_attempt
from app.trust.score import check_safety_gate, video_score
from app.video.frames import extract_frames

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

    # Read-only attempt status query (pure non-blocking database read)
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


def _parse_step_ids(raw_step_ids: Any) -> List[str]:
    if isinstance(raw_step_ids, list):
        out = []
        for item in raw_step_ids:
            if isinstance(item, str):
                try:
                    parsed = json.loads(item)
                    if isinstance(parsed, list):
                        out.extend([str(x).strip() for x in parsed if str(x).strip()])
                    elif parsed:
                        out.append(str(parsed).strip())
                except Exception:
                    for part in item.split(","):
                        if part.strip():
                            out.append(part.strip())
            elif item:
                out.append(str(item).strip())
        return list(dict.fromkeys(out))

    if isinstance(raw_step_ids, str):
        try:
            parsed = json.loads(raw_step_ids)
            if isinstance(parsed, list):
                return list(dict.fromkeys([str(x).strip() for x in parsed if str(x).strip()]))
            elif parsed:
                return [str(parsed).strip()]
        except Exception:
            parts = [p.strip() for p in raw_step_ids.split(",") if p.strip()]
            return list(dict.fromkeys(parts))

    return []


@router.post("/attempts/{attempt_id}/rerecord", response_model=APIResponse[dict])
async def rerecord_failed_steps(
    attempt_id: str,
    file: UploadFile = File(...),
    step_ids: Optional[str] = Form(default=None),
    db: Session = Depends(get_session),
):
    """
    Accepts a video clip demonstrating specific re-recorded steps.
    Extracts frames, performs AI analysis (Prompt 1), merges results
    into existing attempt steps, recalculates video score and review decision.
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

    parsed_step_ids = _parse_step_ids(step_ids)
    if not parsed_step_ids:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="STEP_IDS_REQUIRED",
                    message="At least one step_id must be provided to re-record.",
                    hint="Provide step_ids as a JSON list or comma-separated string.",
                ),
            ).model_dump(),
        )

    # 1. Setup save locations
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    videos_dir = data_dir / "videos"
    rerecord_frames_dir = data_dir / "frames" / f"{attempt_id}_rerecord"
    videos_dir.mkdir(parents=True, exist_ok=True)
    rerecord_frames_dir.mkdir(parents=True, exist_ok=True)

    dest_file = videos_dir / f"{attempt_id}_rerecord.webm"

    try:
        with open(dest_file, "wb") as f:
            while chunk := await file.read(65536):
                f.write(chunk)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="SAVE_FAILED",
                    message="Failed to save re-recorded video.",
                    hint=str(e),
                ),
            ).model_dump(),
        )

    # 2. Extract frames
    frame_paths = []
    try:
        frame_paths = extract_frames(dest_file, rerecord_frames_dir, max_frames=12, max_dimension=768)
    except Exception as e:
        existing_frames = sorted([str(p).replace("\\", "/") for p in rerecord_frames_dir.glob("*.jpg")])
        if existing_frames:
            frame_paths = existing_frames
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=APIResponse[None](
                    ok=False,
                    data=None,
                    error=APIError(
                        code="FRAME_EXTRACTION_FAILED",
                        message="Could not extract frames from re-recorded video.",
                        hint=str(e),
                    ),
                ).model_dump(),
            )

    # 3. Run AI analysis (Prompt 1) on new frames
    blueprint = load_blueprint(attempt.skill_id)
    provider = get_default_ai()
    user_prompt = build_analyzer_user_prompt(
        blueprint_steps=blueprint.steps,
        safety_items=blueprint.safety_items,
        challenge_code=attempt.challenge_code,
    )
    raw_response = provider.generate_content(
        prompt=user_prompt,
        system_instruction=ANALYZER_SYSTEM_PROMPT,
        image_paths=frame_paths,
    )
    ai_parsed = validate_json(raw_response, AnalyzerResult)
    new_ai_result = ai_parsed.model_dump()

    # 4. Overwrite results for the specified step_ids
    existing_ai_result = json.loads(attempt.ai_result_json) if attempt.ai_result_json else {"steps": []}
    existing_steps_map = {s["id"]: s for s in existing_ai_result.get("steps", [])}
    new_steps_map = {s["id"]: s for s in new_ai_result.get("steps", [])}

    for sid in parsed_step_ids:
        if sid in new_steps_map:
            existing_steps_map[sid] = new_steps_map[sid]

    # Reconstruct blueprint steps
    step_meta = {
        s.id: {
            "title": s.title,
            "critical": s.critical,
            "safety_critical": s.safety_critical,
        }
        for s in blueprint.steps
    }

    evaluated_steps = []
    for bp_step in blueprint.steps:
        sid = bp_step.id
        st = existing_steps_map.get(sid, {
            "id": sid,
            "verdict": "pass",
            "confidence": 0.8,
            "evidence_frames": [],
            "note": "Re-recorded step",
        })
        meta = step_meta.get(sid, {})
        evaluated_steps.append({
            **st,
            "title": meta.get("title", sid),
            "critical": meta.get("critical", False),
            "safety_critical": meta.get("safety_critical", False),
        })

    existing_ai_result["steps"] = [
        {k: v for k, v in s.items() if k not in ("title", "critical", "safety_critical")}
        for s in evaluated_steps
    ]
    if new_ai_result.get("challenge_code_seen"):
        existing_ai_result["challenge_code_seen"] = True
    if new_ai_result.get("safety_items_seen"):
        existing_ai_result["safety_items_seen"] = list(
            set(existing_ai_result.get("safety_items_seen", []) + new_ai_result.get("safety_items_seen", []))
        )

    # 5. Recalculate score and review decision
    calculated_score = video_score(evaluated_steps, blueprint.steps)
    safety_passed, failed_safety = check_safety_gate(evaluated_steps, blueprint.steps)
    failed_critical = [
        s["id"] for s in evaluated_steps
        if s.get("critical") and s.get("verdict") in ("fail", "unclear")
    ]
    rerecord_candidates = [
        s["id"] for s in evaluated_steps if s.get("verdict") in ("fail", "unclear")
    ]
    fraud_flags = json.loads(attempt.fraud_flags_json) if attempt.fraud_flags_json else []

    if fraud_flags:
        decision = "reject"
        reason = f"Fraud flags detected ({len(fraud_flags)} flag(s))."
    elif not safety_passed or failed_critical:
        decision = "needs_rerecord"
        reason = f"Critical step(s) failed or unclear ({', '.join(rerecord_candidates)}). Re-recording required."
    elif calculated_score < 70.0:
        decision = "reject"
        reason = f"Video score {calculated_score:.1f}% is below 70% passing threshold."
    else:
        decision = "accept"
        reason = f"Demonstration verified with score {calculated_score:.1f}%."

    agent_log = [
        f"Re-recorded step(s): {', '.join(parsed_step_ids)}",
        f"N1 Safety Gate: {'PASSED' if safety_passed else 'TRIGGERED (Capped score at 0)'}",
        f"Recalculated video score: {calculated_score:.1f}%",
        f"Updated review decision: {decision.upper()} - {reason}",
    ]

    attempt.ai_result_json = json.dumps(existing_ai_result)
    attempt.video_score = calculated_score
    attempt.decision = decision
    attempt.status = "reviewed"
    attempt.updated_at = utc_now()

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return APIResponse[dict](
        ok=True,
        data={
            "attempt_id": attempt.id,
            "status": attempt.status,
            "video_score": calculated_score,
            "decision": decision,
            "steps": evaluated_steps,
            "agent_log": agent_log,
            "rerecorded_steps": parsed_step_ids,
        },
        error=None,
    )
