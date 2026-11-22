import random
import string
from sqlmodel import Session
from app.models import Attempt


def generate_challenge_code() -> str:
    """Generate a random 4-character uppercase alphanumeric code (e.g. A7K2)."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=4))


def create_attempt(worker_id: str, skill_id: str, db: Session) -> Attempt:
    """Create a new Attempt row with status 'interviewing' and unique challenge code."""
    code = generate_challenge_code()
    attempt = Attempt(
        worker_id=worker_id,
        skill_id=skill_id,
        challenge_code=code,
        status="interviewing",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt
