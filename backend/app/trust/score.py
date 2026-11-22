from typing import Any, Dict, List, Optional, Tuple


def check_safety_gate(
    steps: List[Dict[str, Any]],
    blueprint_steps: Optional[List[Any]] = None,
) -> Tuple[bool, List[str]]:
    """
    N1 Safety Gate rule:
    Checks if any safety_critical step has a verdict of 'fail' or 'unclear'.
    Returns: (passed: bool, failed_safety_step_ids: list[str])
    """
    meta_map: Dict[str, Dict[str, bool]] = {}
    if blueprint_steps:
        for b_step in blueprint_steps:
            s_id = getattr(b_step, "id", None) or (b_step.get("id") if isinstance(b_step, dict) else str(b_step))
            meta_map[s_id] = {
                "critical": getattr(b_step, "critical", None) or (b_step.get("critical", False) if isinstance(b_step, dict) else False),
                "safety_critical": getattr(b_step, "safety_critical", None) or (b_step.get("safety_critical", False) if isinstance(b_step, dict) else False),
            }

    failed_safety_ids: List[str] = []
    for step in steps:
        s_id = step.get("id")
        is_safety = meta_map.get(s_id, {}).get("safety_critical", step.get("safety_critical", False))
        verdict = step.get("verdict", "").lower()

        if is_safety and verdict in ("fail", "unclear"):
            failed_safety_ids.append(s_id)

    return len(failed_safety_ids) == 0, failed_safety_ids


def video_score(
    steps: List[Dict[str, Any]],
    blueprint_steps: Optional[List[Any]] = None,
) -> float:
    """
    Computes deterministic video score (0 - 100):
    - Critical steps weigh double (weight 2.0 vs 1.0).
    - 'pass' = full credit (1.0 * weight).
    - 'unclear' = half credit (0.5 * weight).
    - 'fail' = zero credit.
    - N1 Safety Gate: If any safety_critical step is 'fail' or 'unclear', score is capped at 0.0 immediately.
    """
    if not steps:
        return 0.0

    meta_map: Dict[str, Dict[str, bool]] = {}
    if blueprint_steps:
        for b_step in blueprint_steps:
            s_id = getattr(b_step, "id", None) or (b_step.get("id") if isinstance(b_step, dict) else str(b_step))
            meta_map[s_id] = {
                "critical": getattr(b_step, "critical", None) or (b_step.get("critical", False) if isinstance(b_step, dict) else False),
                "safety_critical": getattr(b_step, "safety_critical", None) or (b_step.get("safety_critical", False) if isinstance(b_step, dict) else False),
            }

    # First evaluate N1 Safety Gate
    for step in steps:
        s_id = step.get("id")
        is_safety = meta_map.get(s_id, {}).get("safety_critical", step.get("safety_critical", False))
        verdict = step.get("verdict", "").lower()

        if is_safety and verdict in ("fail", "unclear"):
            return 0.0

    total_possible = 0.0
    total_earned = 0.0

    for step in steps:
        s_id = step.get("id")
        is_critical = meta_map.get(s_id, {}).get("critical", step.get("critical", False))
        weight = 2.0 if is_critical else 1.0
        total_possible += weight

        verdict = step.get("verdict", "").lower()
        if verdict == "pass":
            total_earned += weight * 1.0
        elif verdict == "unclear":
            total_earned += weight * 0.5
        elif verdict == "fail":
            total_earned += 0.0

    if total_possible <= 0.0:
        return 0.0

    score = (total_earned / total_possible) * 100.0
    return round(score, 1)
