"""
backend/app/trust/weights.py

Deterministic calculation of witness vouch weights according to PRD Section 6:
- Role base:
  * peer: 1.0
  * trainer: 1.5
  * employer: 1.2
  * customer: 0.8
  * other/default: 1.0
- Multipliers:
  * has_credential: x 1.5 (if witness holds own credential in same trade)
  * is_reciprocal: x 0.5 (reciprocal vouch with this worker)
  * not seen_in_person: x 0.5 ("did not see in person")
- Zero-weight overrides:
  * same device/IP as the worker -> 0.0
  * duplicate device among witnesses for this attempt -> 0.0 (only first counts)
  * verdict == "needs_work" (or != "yes") -> 0.0
"""
from typing import Optional


ROLE_BASE_WEIGHTS: dict[str, float] = {
    "peer": 1.0,
    "trainer": 1.5,
    "employer": 1.2,
    "customer": 0.8,
}


def calculate_weight(
    role: str,
    has_credential: bool = False,
    is_reciprocal: bool = False,
    seen_in_person: bool = True,
    same_device_as_worker: bool = False,
    device_fp: Optional[str] = None,
    existing_vouch_device_fps: Optional[list[str]] = None,
    verdict: str = "yes",
) -> float:
    """
    Computes deterministic weight for a vouch.
    Returns 0.0 under fraud/self-vouch/duplicate-device conditions or if verdict != 'yes'.
    Otherwise applies base weight and documented multipliers, rounded to 2 decimal places.
    """
    # 1. Zero-weight overrides
    # Verdict must be 'yes' to count towards trust weight
    if verdict.strip().lower() != "yes":
        return 0.0

    # Same device as worker -> collusion/self-vouch risk
    if same_device_as_worker:
        return 0.0

    # Duplicate device fingerprint among existing vouches -> only first counts
    if device_fp and existing_vouch_device_fps:
        clean_fp = device_fp.strip().lower()
        clean_existing = [fp.strip().lower() for fp in existing_vouch_device_fps if fp]
        if clean_fp and clean_fp in clean_existing:
            return 0.0

    # 2. Base role weight
    role_key = role.strip().lower()
    base_weight = ROLE_BASE_WEIGHTS.get(role_key, 1.0)

    # 3. Multipliers
    weight = base_weight

    if has_credential:
        weight *= 1.5

    if is_reciprocal:
        weight *= 0.5

    if not seen_in_person:
        weight *= 0.5

    return round(weight, 2)
