import logging
from typing import Optional
from sqlmodel import Session, select

from app.agent.prompts import (
    build_interviewer_system_prompt,
    build_interviewer_user_prompt,
)
from app.agent.state import AnswerRecord, InterviewState
from app.ai.base import BaseAI
from app.ai.cache import AICache
from app.ai.fallback import FallbackAI
from app.ai.gemini import GeminiAI
from app.ai.mock import MockAI
from app.ai.utils import InterviewerResult, validate_json
from app.blueprints.loader import load_blueprint
from app.config import settings
from app.models import Attempt, Worker, utc_now
from app.schemas import InterviewResponse

logger = logging.getLogger(__name__)


def get_default_ai() -> BaseAI:
    """Return the configured AI provider with cache and fallback."""
    cache = AICache()
    if settings.DEMO_MODE or not settings.GEMINI_API_KEY:
        return FallbackAI([MockAI()], cache=cache)
    return FallbackAI([GeminiAI(), MockAI()], cache=cache)


def run_interview_step(
    attempt: Attempt,
    answer: Optional[str],
    db: Session,
    ai: Optional[BaseAI] = None,
) -> InterviewResponse:
    """
    State machine step for the interview phase.
    Evaluates worker answers with AI against the skill blueprint,
    manages follow-ups (up to 3 max), and transitions attempt to 'awaiting_video'.
    """
    blueprint = load_blueprint(attempt.skill_id)
    scenario_questions = blueprint.scenario_questions
    total_questions = len(scenario_questions)

    # Fetch worker for localized language preferences
    worker = db.exec(select(Worker).where(Worker.id == attempt.worker_id)).first()
    language = worker.language if worker and worker.language else "English"

    # Initialize or load interview state
    if attempt.interview_json:
        try:
            state = InterviewState.model_validate_json(attempt.interview_json)
        except Exception as e:
            logger.warning(f"Failed to parse existing interview_json, resetting state: {e}")
            state = InterviewState()
    else:
        state = InterviewState()

    # If already marked done, return completion
    if state.is_done:
        return InterviewResponse(
            question=None,
            done=True,
            progress={"current": total_questions, "total": total_questions},
        )

    ai_provider = ai or get_default_ai()

    # Case 1: First call or fetching current question (no answer provided)
    if answer is None or not answer.strip():
        if state.active_question_text:
            question_text = state.active_question_text
        elif state.current_question_index < total_questions:
            question_text = scenario_questions[state.current_question_index].text
            state.active_question_text = question_text
        else:
            state.is_done = True
            question_text = None

        attempt.interview_json = state.model_dump_json()
        attempt.updated_at = utc_now()
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return InterviewResponse(
            question=question_text,
            done=state.is_done,
            progress={
                "current": min(state.current_question_index + 1, max(total_questions, 1)),
                "total": total_questions,
            },
        )

    # Case 2: Worker submitted an answer
    q_index = state.current_question_index
    if q_index >= total_questions:
        state.is_done = True
        attempt.status = "awaiting_video"
        attempt.interview_json = state.model_dump_json()
        attempt.updated_at = utc_now()
        db.add(attempt)
        db.commit()
        return InterviewResponse(
            question=None,
            done=True,
            progress={"current": total_questions, "total": total_questions},
        )

    current_scenario = scenario_questions[q_index]
    asked_text = state.active_question_text or current_scenario.text

    # Build prompts and query AI
    system_prompt = build_interviewer_system_prompt(trade=blueprint.trade, language=language)
    user_prompt = build_interviewer_user_prompt(
        question_text=asked_text,
        worker_answer=answer.strip(),
        expected_points=current_scenario.expected_points,
        common_mistakes=blueprint.common_mistakes,
        follow_ups_used=state.follow_up_count,
        max_followups=3,
    )

    raw_ai_res = ai_provider.generate_content(prompt=user_prompt, system_instruction=system_prompt)
    interviewer_eval = validate_json(raw_ai_res, InterviewerResult)

    # Record answer in state
    answer_record = AnswerRecord(
        question_index=q_index,
        question_text=asked_text,
        worker_answer=answer.strip(),
        score=interviewer_eval.score,
        missing_points=interviewer_eval.missing_points,
        is_followup=(state.active_question_text != current_scenario.text),
    )
    state.answers.append(answer_record.model_dump())
    state.scores.append(interviewer_eval.score)

    # Determine next step
    if interviewer_eval.next.type == "followup" and state.follow_up_count < 3:
        state.follow_up_count += 1
        state.active_question_text = interviewer_eval.next.text
        next_question = interviewer_eval.next.text
        done = False
        progress_current = state.current_question_index + 1
    else:
        # Move to next scenario question
        state.current_question_index += 1
        if state.current_question_index < total_questions:
            next_scenario = scenario_questions[state.current_question_index]
            state.active_question_text = next_scenario.text
            next_question = next_scenario.text
            done = False
            progress_current = state.current_question_index + 1
        else:
            # All scenario questions completed
            state.is_done = True
            state.active_question_text = None
            next_question = None
            done = True
            progress_current = total_questions

            # Update attempt status and final interview score
            attempt.status = "awaiting_video"
            if state.scores:
                attempt.interview_score = round(float(sum(state.scores) / len(state.scores)), 1)
            else:
                attempt.interview_score = 0.0

    attempt.interview_json = state.model_dump_json()
    attempt.updated_at = utc_now()
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return InterviewResponse(
        question=next_question,
        done=done,
        progress={"current": progress_current, "total": total_questions},
    )
