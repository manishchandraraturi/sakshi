from typing import Any, List, Optional

ANALYZER_SYSTEM_PROMPT = (
    "You are a vocational skill evidence checker. You receive: a skill BLUEPRINT "
    "(ordered steps with visual criteria, critical flags, safety items), up to 12 timestamped "
    "frames from one worker video, a CHALLENGE_CODE, and an optional TRANSCRIPT.\n"
    'For each blueprint step decide: "pass", "fail" or "unclear", with confidence 0-1, '
    'the frame indices that are your evidence, and one short note. Use "unclear" when evidence '
    "is missing, blurry or ambiguous; never assume.\n"
    "Also report: challenge_code_seen (true only if the code is visible on screen/paper or present in TRANSCRIPT), "
    'safety_items_seen (list of blueprint safety item ids seen), video_quality ("good"|"poor") with reason.\n'
    "Judge only against the blueprint. Do not invent steps. Output ONLY JSON in this schema:\n"
    '{"steps":[{"id":str,"verdict":"pass|fail|unclear","confidence":float,"evidence_frames":[int],"note":str}],'
    '"challenge_code_seen":bool,"safety_items_seen":[str],"video_quality":{"rating":"good|poor","reason":str}}'
)


def build_analyzer_user_prompt(
    blueprint_steps: List[Any],
    safety_items: List[str],
    challenge_code: str,
    transcript: Optional[str] = None,
) -> str:
    """Build the user prompt for Prompt 1 (Frame analyzer)."""
    steps_formatted = []
    for step in blueprint_steps:
        s_id = getattr(step, "id", None) or (step.get("id") if isinstance(step, dict) else str(step))
        s_title = getattr(step, "title", None) or (step.get("title") if isinstance(step, dict) else "")
        s_crit = getattr(step, "critical", None) or (step.get("critical") if isinstance(step, dict) else False)
        s_safe = getattr(step, "safety_critical", None) or (step.get("safety_critical") if isinstance(step, dict) else False)
        s_vis = getattr(step, "visual_criteria", None) or (step.get("visual_criteria") if isinstance(step, dict) else "")
        steps_formatted.append(
            f"- Step ID: {s_id}\n"
            f"  Title: {s_title}\n"
            f"  Visual Criteria: {s_vis}\n"
            f"  Critical: {s_crit}, Safety Critical: {s_safe}"
        )

    prompt = (
        f"CHALLENGE_CODE TO VERIFY: {challenge_code}\n\n"
        f"BLUEPRINT REQUIRED SAFETY ITEMS: {', '.join(safety_items) if safety_items else 'None'}\n\n"
        f"BLUEPRINT ORDERED STEPS:\n"
        + "\n\n".join(steps_formatted)
        + "\n\n"
    )

    if transcript:
        prompt += f"OPTIONAL AUDIO TRANSCRIPT: {transcript}\n\n"

    prompt += (
        "Inspect the provided video frames carefully. For every step listed above, provide a verdict "
        "('pass', 'fail', or 'unclear') citing evidence frame indices. "
        "Confirm whether the challenge code was visible on screen or paper. "
        "Output ONLY valid JSON matching the requested schema."
    )
    return prompt


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
