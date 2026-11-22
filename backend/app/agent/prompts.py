import json
from typing import List

INTERVIEWER_SYSTEM_PROMPT = (
    "You are a friendly skills interviewer for a {trade} in {language}. "
    "Use ONLY the blueprint's scenario questions and common mistakes. "
    "Ask one short question at a time in simple words. "
    "If the previous answer is vague or misses a key point from the blueprint's expected_points, "
    "ask ONE follow-up (max 3 follow-ups in total). Score each answer 0-100 against expected_points. "
    "Output ONLY JSON:\n"
    '{{"score":int,"missing_points":[str],"next":{{"type":"question|followup|done","text":str}}}}'
)


def build_interviewer_system_prompt(trade: str, language: str = "English") -> str:
    """Build the system prompt for the skills interviewer agent."""
    return INTERVIEWER_SYSTEM_PROMPT.format(trade=trade, language=language)


def build_interviewer_user_prompt(
    question_text: str,
    worker_answer: str,
    expected_points: List[str],
    common_mistakes: List[str],
    follow_ups_used: int = 0,
    max_followups: int = 3,
) -> str:
    """Build the user prompt evaluating the worker's answer against blueprint criteria."""
    return (
        f"QUESTION ASKED: {question_text}\n\n"
        f"WORKER'S ANSWER: {worker_answer}\n\n"
        f"BLUEPRINT EXPECTED POINTS:\n"
        + "\n".join(f"- {pt}" for pt in expected_points)
        + "\n\n"
        f"BLUEPRINT COMMON MISTAKES TO WATCH FOR:\n"
        + "\n".join(f"- {m}" for m in common_mistakes)
        + f"\n\nFOLLOW-UPS USED SO FAR: {follow_ups_used} (Max allowed: {max_followups}).\n\n"
        "Score the worker's answer from 0 to 100 based on how many expected points were covered. "
        "List any missing points. "
        "If expected points are missing or vague, and follow_ups_used < 3, set next.type='followup' "
        "with an encouraging follow-up question. "
        "Otherwise, if answer is complete or max follow-ups reached, set next.type='question' or 'done'. "
        "Output ONLY valid JSON matching the schema."
    )
