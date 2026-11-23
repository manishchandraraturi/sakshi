"""
backend/app/seed.py

Database seed script for demo data in Project SAKSHI.
Can be executed directly via:
    python -m app.seed

Clears the database and seeds 3 distinct workers with authentic
Ed25519-signed credentials:
1. Ravi Kumar (Electrician, Tier 3 Trusted, Score 92)
2. Suresh Patil (Mason, Tier 2 Witnessed, Score 78)
3. Anita Sharma (Plumber, Tier 1 Demonstrated, Score 71)
"""
import json
import uuid
from datetime import timedelta
from sqlmodel import Session, SQLModel, delete

from app.crypto.sign import sign_payload
from app.db import engine
from app.models import (
    Attempt,
    AuditLog,
    Credential,
    Vouch,
    WitnessInvite,
    Worker,
    utc_now,
)
from app.trust.tiers import calculate_tier, calculate_trust_score


def seed_database():
    """
    Clears tables and inserts 3 fully formed demo workers with verified
    practical skill assessments, witness vouches, and cryptographic credentials.
    """
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # 1. Clear existing database tables
        session.exec(delete(Vouch))
        session.exec(delete(WitnessInvite))
        session.exec(delete(Credential))
        session.exec(delete(Attempt))
        session.exec(delete(Worker))
        session.exec(delete(AuditLog))
        session.commit()

        now = utc_now()
        credentials_seeded = []

        # ============================================================
        # Worker 1: Ravi Kumar — Tier 3: Trusted (Electrician)
        # ============================================================
        w1 = Worker(
            name="Ravi Kumar",
            language="kn",
            area="Bangalore South",
            phone_optional="9876543210",
            device_fp="fp_ravi_samsung_a14",
            token="tok_ravi_kumar_demo",
            consent_at=now,
            created_at=now,
        )
        session.add(w1)
        session.commit()
        session.refresh(w1)

        att1 = Attempt(
            worker_id=w1.id,
            skill_id="electrician_socket",
            status="finalized",
            challenge_code="R7K2",
            video_score=88.0,
            interview_score=87.0,
            decision="accept",
            video_sha256="4a5c6d7e8f901234567890abcdef1234567890abcdef1234567890abcdef12",
            created_at=now - timedelta(days=2),
            updated_at=now,
        )
        session.add(att1)
        session.commit()
        session.refresh(att1)

        # Vouches for Ravi: Trainer (1.5) + Employer with credential (1.8) = 3.3 weight
        inv1_1 = WitnessInvite(attempt_id=att1.id, token="tok_inv_ramesh_trainer", used_at=now)
        inv1_2 = WitnessInvite(attempt_id=att1.id, token="tok_inv_mohan_employer", used_at=now)
        session.add(inv1_1)
        session.add(inv1_2)
        session.commit()
        session.refresh(inv1_1)
        session.refresh(inv1_2)

        vouch1_1 = Vouch(
            invite_id=inv1_1.id,
            attempt_id=att1.id,
            witness_name="Master Craftsman Ramesh",
            role="trainer",
            seen_in_person=True,
            known_years_bucket="3+",
            would_hire=True,
            verdict="yes",
            weight=1.5,
            created_at=now - timedelta(days=1),
        )
        vouch1_2 = Vouch(
            invite_id=inv1_2.id,
            attempt_id=att1.id,
            witness_name="Contractor Mohan",
            role="employer",
            seen_in_person=True,
            known_years_bucket="3+",
            would_hire=True,
            verdict="yes",
            weight=1.8,
            created_at=now - timedelta(hours=12),
        )
        session.add(vouch1_1)
        session.add(vouch1_2)
        session.commit()

        tier1 = calculate_tier(
            video_score=88.0,
            critical_steps_pass=True,
            has_fraud_flag=False,
            safety_gate_failed=False,
            witness_weight=3.3,
            distinct_witnesses=2,
            has_trainer_or_employer=True,
        )
        score1 = calculate_trust_score(88.0, 87.0, 3.3)  # 92

        cred1_id = str(uuid.uuid4())
        valid_until_1 = (now + timedelta(days=365)).isoformat()
        payload1 = {
            "cred_id": cred1_id,
            "worker_name": "Ravi Kumar",
            "area": "Bangalore South",
            "trade": "Electrician",
            "skill": "Socket wiring & continuity test",
            "tier": tier1,
            "trust_score": score1,
            "issued_at": now.isoformat(),
            "valid_until": valid_until_1,
            "evidence_sha256": att1.video_sha256,
            "witness_count": 2,
        }
        sig1, _ = sign_payload(payload1)

        cred1 = Credential(
            id=cred1_id,
            attempt_id=att1.id,
            worker_id=w1.id,
            skill_id=att1.skill_id,
            tier=tier1,
            trust_score=float(score1),
            payload_json=json.dumps(payload1, sort_keys=True, separators=(",", ":")),
            signature_b64=sig1,
            evidence_sha256=att1.video_sha256,
            issued_at=now,
            revoked=False,
        )
        session.add(cred1)
        session.commit()
        credentials_seeded.append((w1.name, "Electrician", tier1, score1, cred1_id))

        # ============================================================
        # Worker 2: Suresh Patil — Tier 2: Witnessed (Mason)
        # ============================================================
        w2 = Worker(
            name="Suresh Patil",
            language="hi",
            area="Delhi West",
            phone_optional="9812345678",
            device_fp="fp_suresh_redmi_12",
            token="tok_suresh_patil_demo",
            consent_at=now,
            created_at=now,
        )
        session.add(w2)
        session.commit()
        session.refresh(w2)

        att2 = Attempt(
            worker_id=w2.id,
            skill_id="mason_wall",
            status="finalized",
            challenge_code="M3P9",
            video_score=92.0,
            interview_score=90.0,
            decision="accept",
            video_sha256="b8c7d6e5f4a3210987654321fedcba0987654321fedcba0987654321fedcba09",
            created_at=now - timedelta(days=3),
            updated_at=now,
        )
        session.add(att2)
        session.commit()
        session.refresh(att2)

        inv2_1 = WitnessInvite(attempt_id=att2.id, token="tok_inv_anil_peer", used_at=now)
        session.add(inv2_1)
        session.commit()
        session.refresh(inv2_1)

        vouch2_1 = Vouch(
            invite_id=inv2_1.id,
            attempt_id=att2.id,
            witness_name="Anil Kumar (Senior Mason)",
            role="peer",
            seen_in_person=True,
            known_years_bucket="1-3",
            would_hire=True,
            verdict="yes",
            weight=1.6,
            created_at=now - timedelta(days=2),
        )
        session.add(vouch2_1)
        session.commit()

        tier2 = calculate_tier(
            video_score=92.0,
            critical_steps_pass=True,
            has_fraud_flag=False,
            safety_gate_failed=False,
            witness_weight=1.6,
            distinct_witnesses=1,
            has_trainer_or_employer=False,
        )
        score2 = calculate_trust_score(92.0, 90.0, 1.6)  # 78

        cred2_id = str(uuid.uuid4())
        valid_until_2 = (now + timedelta(days=365)).isoformat()
        payload2 = {
            "cred_id": cred2_id,
            "worker_name": "Suresh Patil",
            "area": "Delhi West",
            "trade": "Mason",
            "skill": "Brick wall alignment & plumb test",
            "tier": tier2,
            "trust_score": score2,
            "issued_at": now.isoformat(),
            "valid_until": valid_until_2,
            "evidence_sha256": att2.video_sha256,
            "witness_count": 1,
        }
        sig2, _ = sign_payload(payload2)

        cred2 = Credential(
            id=cred2_id,
            attempt_id=att2.id,
            worker_id=w2.id,
            skill_id=att2.skill_id,
            tier=tier2,
            trust_score=float(score2),
            payload_json=json.dumps(payload2, sort_keys=True, separators=(",", ":")),
            signature_b64=sig2,
            evidence_sha256=att2.video_sha256,
            issued_at=now,
            revoked=False,
        )
        session.add(cred2)
        session.commit()
        credentials_seeded.append((w2.name, "Mason", tier2, score2, cred2_id))

        # ============================================================
        # Worker 3: Anita Sharma — Tier 1: Demonstrated (Plumber)
        # ============================================================
        w3 = Worker(
            name="Anita Sharma",
            language="hi",
            area="Bangalore North",
            phone_optional="9701234567",
            device_fp="fp_anita_vivo_y20",
            token="tok_anita_sharma_demo",
            consent_at=now,
            created_at=now,
        )
        session.add(w3)
        session.commit()
        session.refresh(w3)

        att3 = Attempt(
            worker_id=w3.id,
            skill_id="plumber_joint",
            status="finalized",
            challenge_code="P4X1",
            video_score=92.0,
            interview_score=96.0,
            decision="accept",
            video_sha256="c7b6a59483726150493827160594837261504938271605948372615049382716",
            created_at=now - timedelta(days=1),
            updated_at=now,
        )
        session.add(att3)
        session.commit()
        session.refresh(att3)

        inv3_1 = WitnessInvite(attempt_id=att3.id, token="tok_inv_priya_customer", used_at=now)
        session.add(inv3_1)
        session.commit()
        session.refresh(inv3_1)

        vouch3_1 = Vouch(
            invite_id=inv3_1.id,
            attempt_id=att3.id,
            witness_name="Priya Client",
            role="customer",
            seen_in_person=True,
            known_years_bucket="<1",
            would_hire=True,
            verdict="yes",
            weight=0.9,
            created_at=now - timedelta(hours=6),
        )
        session.add(vouch3_1)
        session.commit()

        tier3 = calculate_tier(
            video_score=92.0,
            critical_steps_pass=True,
            has_fraud_flag=False,
            safety_gate_failed=False,
            witness_weight=0.9,
            distinct_witnesses=1,
            has_trainer_or_employer=False,
        )
        score3 = calculate_trust_score(92.0, 96.0, 0.9)  # 71

        cred3_id = str(uuid.uuid4())
        valid_until_3 = (now + timedelta(days=365)).isoformat()
        payload3 = {
            "cred_id": cred3_id,
            "worker_name": "Anita Sharma",
            "area": "Bangalore North",
            "trade": "Plumber",
            "skill": "Pipe joint & pressure leak test",
            "tier": tier3,
            "trust_score": score3,
            "issued_at": now.isoformat(),
            "valid_until": valid_until_3,
            "evidence_sha256": att3.video_sha256,
            "witness_count": 1,
        }
        sig3, _ = sign_payload(payload3)

        cred3 = Credential(
            id=cred3_id,
            attempt_id=att3.id,
            worker_id=w3.id,
            skill_id=att3.skill_id,
            tier=tier3,
            trust_score=float(score3),
            payload_json=json.dumps(payload3, sort_keys=True, separators=(",", ":")),
            signature_b64=sig3,
            evidence_sha256=att3.video_sha256,
            issued_at=now,
            revoked=False,
        )
        session.add(cred3)
        session.commit()
        credentials_seeded.append((w3.name, "Plumber", tier3, score3, cred3_id))

    # Print summary
    print("==============================================================")
    print("SAKSHI SEED COMPLETED SUCCESSFULLY")
    print("==============================================================")
    for name, trade, tier, score, cid in credentials_seeded:
        print(f"- {name} ({trade}) — Tier {tier} (Trust Score: {score})")
        print(f"  Credential ID: {cid}")
        print(f"  Verify URL: http://localhost:5173/c/{cid}")
    print("==============================================================")


if __name__ == "__main__":
    seed_database()
