import json
import logging
from typing import Any, Dict, List, Optional
from sqlmodel import Session, select

from app.agent.loop import get_default_ai
from app.agent.prompts import build_coach_system_prompt, build_coach_user_prompt
from app.ai.base import BaseAI
from app.ai.utils import CoachResult, validate_json
from app.models import Attempt, Worker

logger = logging.getLogger(__name__)


def generate_coaching(
    attempt: Attempt,
    blueprint: Any,
    ai_provider: Optional[BaseAI] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Executes Prompt 3 (Coach/explainer).
    Takes attempt analysis results, identifies failed/unclear steps,
    and runs Prompt 3 via the AI provider.
    Returns {"summary": str, "next_actions": [str], "unclear_steps_tips": [{"step_id": str, "tip": str}]}.
    """
    # 1. Determine worker language
    language = "English"
    if db and attempt.worker_id:
        try:
            worker = db.exec(select(Worker).where(Worker.id == attempt.worker_id)).first()
            if worker and worker.language:
                language = worker.language
        except Exception as e:
            logger.warning(f"Failed to lookup worker language: {e}")

    # 2. Extract steps requiring coaching
    unclear_or_failed: List[Dict[str, Any]] = []
    if attempt.ai_result_json:
        try:
            ai_data = json.loads(attempt.ai_result_json)
            steps = ai_data.get("steps", [])
            step_titles = {s.id: s.title for s in blueprint.steps} if hasattr(blueprint, "steps") else {}
            for st in steps:
                verdict = str(st.get("verdict", "")).lower()
                if verdict in ("fail", "unclear"):
                    unclear_or_failed.append(
                        {
                            "id": st.get("id"),
                            "title": step_titles.get(st.get("id"), st.get("id")),
                            "verdict": verdict,
                            "note": st.get("note", ""),
                        }
                    )
        except Exception as e:
            logger.warning(f"Error parsing ai_result_json for coaching: {e}")

    # 3. Build prompts
    system_prompt = build_coach_system_prompt(language=language)
    user_prompt = build_coach_user_prompt(
        trade=getattr(blueprint, "trade", "vocational"),
        skill_name=getattr(blueprint, "name", attempt.skill_id),
        decision=attempt.decision or "reviewed",
        score=attempt.video_score or 0.0,
        failed_steps=unclear_or_failed,
        witness_status="Pending witness verifications",
        tier=1 if (attempt.decision == "accept") else 0,
    )

    # 4. Invoke AI provider with fallback
    try:
        provider = ai_provider or get_default_ai()
        raw_response = provider.generate_content(
            prompt=user_prompt,
            system_instruction=system_prompt,
        )
        parsed = validate_json(raw_response, CoachResult)
        return parsed.model_dump()
    except Exception as e:
        logger.warning(f"AI coaching generation failed: {e}. Using deterministic fallback.")
        if unclear_or_failed:
            tips = [
                {
                    "step_id": s["id"],
                    "tip": f"Ensure your hands and tools are clearly framed in good lighting for {s.get('title', s['id'])}.",
                }
                for s in unclear_or_failed
            ]
            actions = [
                "Re-record the steps that were unclear or missed criteria",
                "Ensure challenge code is held steadily in view",
                "Review the blueprint checklist before recording",
            ]
            summary = (
                f"You demonstrated good effort on {getattr(blueprint, 'name', 'the assessment')}. "
                f"{len(unclear_or_failed)} step(s) were unclear or missed key criteria and need re-recording."
            )
        else:
            tips = []
            actions = [
                "Invite trusted peers or trainers to witness your demonstration",
                "Share your credential card on WhatsApp or public profile",
                "Explore next-level vocational skills in your trade",
            ]
            summary = (
                f"Great work! Your demonstration for {getattr(blueprint, 'name', 'the assessment')} "
                "met all required practical standards."
            )

        return {
            "summary": summary,
            "next_actions": actions[:3],
            "unclear_steps_tips": tips,
        }
