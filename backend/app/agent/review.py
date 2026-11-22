import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlmodel import Session

from app.agent.loop import get_default_ai
from app.agent.prompts import ANALYZER_SYSTEM_PROMPT, build_analyzer_user_prompt
from app.ai.base import BaseAI
from app.ai.utils import AnalyzerResult, validate_json
from app.blueprints.loader import load_blueprint
from app.models import Attempt, utc_now
from app.trust.score import check_safety_gate, video_score

logger = logging.getLogger(__name__)


def run_review_decision(
    attempt: Attempt,
    db: Session,
    ai_provider: Optional[BaseAI] = None,
) -> Dict[str, Any]:
    """
    Executes AI video analysis (Prompt 1) on extracted frames,
    computes deterministic video score (with N1 safety gate),
    and evaluates the agent review decision (accept / needs_rerecord / reject).
    Updates the Attempt row with status='reviewed'.
    """
    blueprint = load_blueprint(attempt.skill_id)

    # 1. AI Analysis if not already performed
    if not attempt.ai_result_json:
        data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        frames_dir = data_dir / "frames" / attempt.id
        frame_paths = (
            sorted([str(p).replace("\\", "/") for p in frames_dir.glob("*.jpg")])
            if frames_dir.exists()
            else []
        )

        provider = ai_provider or get_default_ai()
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
        ai_result = ai_parsed.model_dump()
        attempt.ai_result_json = json.dumps(ai_result)
    else:
        ai_result = json.loads(attempt.ai_result_json)

    # 2. Annotate evaluated steps with blueprint metadata
    step_meta = {
        s.id: {
            "title": s.title,
            "critical": s.critical,
            "safety_critical": s.safety_critical,
        }
        for s in blueprint.steps
    }

    evaluated_steps: List[Dict[str, Any]] = []
    for st in ai_result.get("steps", []):
        s_id = st.get("id")
        meta = step_meta.get(s_id, {})
        evaluated_steps.append(
            {
                **st,
                "title": meta.get("title", s_id),
                "critical": meta.get("critical", False),
                "safety_critical": meta.get("safety_critical", False),
            }
        )

    # 3. Calculate deterministic video score
    calculated_score = video_score(evaluated_steps, blueprint.steps)

    # 4. Read fraud flags
    fraud_flags: List[Dict[str, Any]] = (
        json.loads(attempt.fraud_flags_json) if attempt.fraud_flags_json else []
    )

    # 5. Check Safety Gate & Critical Steps
    safety_passed, failed_safety = check_safety_gate(evaluated_steps, blueprint.steps)
    failed_critical = [
        s["id"]
        for s in evaluated_steps
        if s.get("critical") and s.get("verdict") in ("fail", "unclear")
    ]
    rerecord_candidates = [
        s["id"] for s in evaluated_steps if s.get("verdict") in ("fail", "unclear")
    ]

    # 6. Apply Review Decision Rules
    if fraud_flags:
        decision = "reject"
        reason = f"Fraud flags detected ({len(fraud_flags)} flag(s))."
    elif not safety_passed or failed_critical:
        decision = "needs_rerecord"
        reason = (
            f"Critical step(s) failed or unclear ({', '.join(rerecord_candidates)}). "
            "Re-recording required."
        )
    elif calculated_score < 70.0:
        decision = "reject"
        reason = f"Video score {calculated_score:.1f}% is below 70% passing threshold."
    else:
        decision = "accept"
        reason = f"Demonstration verified with score {calculated_score:.1f}%."

    # 7. Formulate Agent Reasoning Log
    agent_log = [
        f"Analyzed video demonstration for skill '{blueprint.name}'",
        f"Challenge code check: {'VERIFIED' if ai_result.get('challenge_code_seen') else 'NOT SEEN'}",
        f"Video quality rating: {ai_result.get('video_quality', {}).get('rating', 'good').upper()}",
        f"N1 Safety Gate: {'PASSED' if safety_passed else 'TRIGGERED (Capped score at 0)'}",
        f"Calculated video score: {calculated_score:.1f}%",
        f"Review decision: {decision.upper()} - {reason}",
    ]

    # 8. Update DB Attempt Row
    attempt.video_score = calculated_score
    attempt.decision = decision
    attempt.status = "reviewed"
    attempt.updated_at = utc_now()

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "decision": decision,
        "video_score": calculated_score,
        "steps": evaluated_steps,
        "rerecord_step_ids": rerecord_candidates if decision == "needs_rerecord" else [],
        "fraud_flags": fraud_flags,
        "agent_log": agent_log,
    }
