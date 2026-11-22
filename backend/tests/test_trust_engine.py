import pytest
from app.trust.tiers import (
    TIER_NAMES,
    calculate_tier,
    calculate_trust_breakdown,
    calculate_trust_score,
)
from app.trust.weights import ROLE_BASE_WEIGHTS, calculate_weight


# --- Table-driven tests for calculate_weight ---
@pytest.mark.parametrize(
    "case_name, kwargs, expected_weight",
    [
        ("peer base", {"role": "peer"}, 1.0),
        ("trainer base", {"role": "trainer"}, 1.5),
        ("employer base", {"role": "employer"}, 1.2),
        ("customer base", {"role": "customer"}, 0.8),
        ("unknown role default", {"role": "other"}, 1.0),
        ("peer with credential", {"role": "peer", "has_credential": True}, 1.5),
        ("trainer with credential", {"role": "trainer", "has_credential": True}, 2.25),
        ("employer with credential", {"role": "employer", "has_credential": True}, 1.8),
        ("customer with credential", {"role": "customer", "has_credential": True}, 1.2),
        ("reciprocal penalty", {"role": "peer", "is_reciprocal": True}, 0.5),
        ("not seen in person penalty", {"role": "peer", "seen_in_person": False}, 0.5),
        (
            "reciprocal + not seen in person",
            {"role": "peer", "is_reciprocal": True, "seen_in_person": False},
            0.25,
        ),
        (
            "trainer + credential + not seen in person",
            {"role": "trainer", "has_credential": True, "seen_in_person": False},
            1.12,  # round(1.5 * 1.5 * 0.5, 2) = 1.12
        ),
        ("same device as worker", {"role": "peer", "same_device_as_worker": True}, 0.0),
        ("verdict needs_work", {"role": "trainer", "verdict": "needs_work"}, 0.0),
        ("verdict invalid", {"role": "trainer", "verdict": "no"}, 0.0),
        (
            "duplicate device fp in existing",
            {
                "role": "peer",
                "device_fp": "fp_duplicate_123",
                "existing_vouch_device_fps": ["fp_first", "fp_duplicate_123"],
            },
            0.0,
        ),
        (
            "unique device fp",
            {
                "role": "peer",
                "device_fp": "fp_unique_456",
                "existing_vouch_device_fps": ["fp_first", "fp_duplicate_123"],
            },
            1.0,
        ),
    ],
)
def test_calculate_weight_cases(case_name, kwargs, expected_weight):
    weight = calculate_weight(**kwargs)
    assert weight == expected_weight, f"Failed on case: {case_name}"


# --- Table-driven tests for calculate_tier ---
@pytest.mark.parametrize(
    "case_name, kwargs, expected_tier",
    [
        # Tier 0 cases
        (
            "fraud flag present",
            {
                "video_score": 90.0,
                "critical_steps_pass": True,
                "has_fraud_flag": True,
                "safety_gate_failed": False,
                "witness_weight": 3.5,
                "distinct_witnesses": 2,
                "has_trainer_or_employer": True,
            },
            0,
        ),
        (
            "critical step failed",
            {
                "video_score": 90.0,
                "critical_steps_pass": False,
                "has_fraud_flag": False,
                "safety_gate_failed": False,
                "witness_weight": 3.5,
                "distinct_witnesses": 2,
                "has_trainer_or_employer": True,
            },
            0,
        ),
        (
            "safety gate failed",
            {
                "video_score": 90.0,
                "critical_steps_pass": True,
                "has_fraud_flag": False,
                "safety_gate_failed": True,
                "witness_weight": 3.5,
                "distinct_witnesses": 2,
                "has_trainer_or_employer": True,
            },
            0,
        ),
        (
            "video score below 70",
            {
                "video_score": 69.9,
                "critical_steps_pass": True,
                "has_fraud_flag": False,
                "safety_gate_failed": False,
                "witness_weight": 3.5,
                "distinct_witnesses": 2,
                "has_trainer_or_employer": True,
            },
            0,
        ),
        # Tier 1 cases (passed baseline, but weight < 1.0)
        (
            "baseline pass zero weight",
            {
                "video_score": 70.0,
                "critical_steps_pass": True,
                "has_fraud_flag": False,
                "safety_gate_failed": False,
                "witness_weight": 0.0,
            },
            1,
        ),
        (
            "baseline pass weight 0.8",
            {
                "video_score": 85.0,
                "critical_steps_pass": True,
                "has_fraud_flag": False,
                "safety_gate_failed": False,
                "witness_weight": 0.8,
            },
            1,
        ),
        # Tier 2 cases (weight >= 1.0 but missing Tier 3 requirements)
        (
            "tier 2 standard (weight 1.0)",
            {
                "video_score": 75.0,
                "critical_steps_pass": True,
                "has_fraud_flag": False,
                "safety_gate_failed": False,
                "witness_weight": 1.0,
            },
            2,
        ),
        (
            "tier 2 weight 2.5",
            {
                "video_score": 80.0,
                "critical_steps_pass": True,
                "has_fraud_flag": False,
                "safety_gate_failed": False,
                "witness_weight": 2.5,
            },
            2,
        ),
        (
            "tier 2 weight >= 3.0 but only 1 witness",
            {
                "video_score": 80.0,
                "critical_steps_pass": True,
                "has_fraud_flag": False,
                "safety_gate_failed": False,
                "witness_weight": 3.0,
                "distinct_witnesses": 1,
                "has_trainer_or_employer": True,
            },
            2,
        ),
        (
            "tier 2 weight >= 3.0 with 2 witnesses but no trainer or employer",
            {
                "video_score": 80.0,
                "critical_steps_pass": True,
                "has_fraud_flag": False,
                "safety_gate_failed": False,
                "witness_weight": 3.2,
                "distinct_witnesses": 2,
                "has_trainer_or_employer": False,
            },
            2,
        ),
        # Tier 3 cases (weight >= 3.0, >= 2 distinct witnesses, >= 1 trainer or employer)
        (
            "tier 3 qualified with trainer",
            {
                "video_score": 85.0,
                "critical_steps_pass": True,
                "has_fraud_flag": False,
                "safety_gate_failed": False,
                "witness_weight": 3.0,
                "distinct_witnesses": 2,
                "has_trainer_or_employer": True,
            },
            3,
        ),
        (
            "tier 3 qualified with excess weight",
            {
                "video_score": 95.0,
                "critical_steps_pass": True,
                "has_fraud_flag": False,
                "safety_gate_failed": False,
                "witness_weight": 5.2,
                "distinct_witnesses": 3,
                "has_trainer_or_employer": True,
            },
            3,
        ),
    ],
)
def test_calculate_tier_cases(case_name, kwargs, expected_tier):
    tier = calculate_tier(**kwargs)
    assert tier == expected_tier, f"Failed on case: {case_name}"


# --- Tests for calculate_trust_score & breakdown ---
def test_calculate_trust_score_bounds_and_formula():
    # 1. Perfect score
    score_perfect = calculate_trust_score(
        video_score=100.0, interview_score=100.0, total_weight=3.0
    )
    assert score_perfect == 100

    # 2. Excess weight caps at 100
    score_excess = calculate_trust_score(
        video_score=100.0, interview_score=100.0, total_weight=6.0
    )
    assert score_excess == 100

    # 3. Zero score
    score_zero = calculate_trust_score(
        video_score=0.0, interview_score=0.0, total_weight=0.0
    )
    assert score_zero == 0

    # 4. Realistic intermediate: video=80, interview=70, weight=1.5
    # Formula: 0.5 * 80 (40) + 0.15 * 70 (10.5) + 0.35 * (1.5/3.0 * 100 = 50 -> 17.5) = 68.0
    score_inter = calculate_trust_score(
        video_score=80.0, interview_score=70.0, total_weight=1.5
    )
    assert score_inter == 68

    # 5. Breakdown check
    breakdown = calculate_trust_breakdown(
        video_score=80.0, interview_score=70.0, total_weight=1.5
    )
    assert breakdown["video_component"] == 40.0
    assert breakdown["interview_component"] == 10.5
    assert breakdown["witness_component"] == 17.5
    assert breakdown["total"] == 68
