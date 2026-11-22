"""
backend/app/trust/tiers.py

Pure functions for computing tiers and display trust scores.
Adheres strictly to PRD Section 6:
- Tier 0: Hard fraud flag, critical steps failed, N1 safety gate failed, or video_score < 70
- Tier 1: Video score >= 70, critical steps pass, no fraud flags, safety gate passed
- Tier 2: Tier 1 + total witness weight >= 1.0
- Tier 3: Tier 1 + total witness weight >= 3.0 + >= 2 distinct witnesses + >= 1 trainer or employer

Display Trust Score (0-100):
0.5 * video + 0.15 * interview + 0.35 * min(100, (weight / 3.0) * 100)
"""
from typing import Any, Dict


TIER_NAMES: Dict[int, str] = {
    0: "Needs retry",
    1: "Demonstrated",
    2: "Witnessed",
    3: "Trusted",
}


def calculate_tier(
    video_score: float,
    critical_steps_pass: bool,
    has_fraud_flag: bool,
    safety_gate_failed: bool,
    witness_weight: float,
    distinct_witnesses: int = 0,
    has_trainer_or_employer: bool = False,
) -> int:
    """
    Computes tier deterministically based on video performance, safety gates,
    fraud detection, and witness vouch parameters.
    """
    # 1. Tier 0 triggers (N1 safety gate, critical step failure, fraud, low score)
    if (
        has_fraud_flag
        or (not critical_steps_pass)
        or safety_gate_failed
        or (video_score < 70.0)
    ):
        return 0

    # 2. Tier 3 (Trusted): weight >= 3.0, >= 2 distinct witnesses, >= 1 trainer or employer
    if witness_weight >= 3.0 and distinct_witnesses >= 2 and has_trainer_or_employer:
        return 3

    # 3. Tier 2 (Witnessed): weight >= 1.0
    if witness_weight >= 1.0:
        return 2

    # 4. Tier 1 (Demonstrated): passed baseline but < 1.0 witness weight
    return 1


def calculate_trust_score(
    video_score: float,
    interview_score: float,
    total_weight: float,
) -> int:
    """
    Computes the display Trust Score (0-100) as:
    0.5 * video + 0.15 * interview + 0.35 * min(100.0, (total_weight / 3.0) * 100.0)
    Returns clamped integer [0, 100].
    """
    witness_component = min(100.0, (max(0.0, total_weight) / 3.0) * 100.0)
    raw = (
        0.5 * max(0.0, video_score)
        + 0.15 * max(0.0, interview_score)
        + 0.35 * witness_component
    )
    clamped = max(0.0, min(100.0, raw))
    return int(round(clamped))


def calculate_trust_breakdown(
    video_score: float,
    interview_score: float,
    total_weight: float,
) -> dict[str, Any]:
    """
    Returns a dictionary of all component contributions to the trust score.
    """
    v_comp = round(0.5 * max(0.0, video_score), 1)
    i_comp = round(0.15 * max(0.0, interview_score), 1)
    w_pct = min(100.0, (max(0.0, total_weight) / 3.0) * 100.0)
    w_comp = round(0.35 * w_pct, 1)
    total = calculate_trust_score(video_score, interview_score, total_weight)

    return {
        "video_score": round(video_score, 1),
        "interview_score": round(interview_score, 1),
        "total_weight": round(total_weight, 2),
        "video_component": v_comp,
        "interview_component": i_comp,
        "witness_component": w_comp,
        "total": total,
    }
