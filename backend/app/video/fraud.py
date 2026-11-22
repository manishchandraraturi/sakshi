import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image
import imagehash
from sqlmodel import Session, select
from app.models import Attempt


def compute_sha256(file_path: Path | str) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_phash(frame_path: Path | str) -> str:
    """Compute perceptual hash (pHash) from an image frame."""
    with Image.open(frame_path) as img:
        return str(imagehash.phash(img))


def detect_fraud(
    video_path: Path | str,
    frame_paths: List[str],
    attempt_id: str,
    source: str,
    db: Session,
) -> Tuple[str, Optional[str], List[Dict[str, Any]]]:
    """
    Compute binary SHA-256 and visual pHash, check database for duplicates,
    and generate fraud detection flags.
    Returns: (file_sha256, phash_str, fraud_flags)
    """
    file_sha256 = compute_sha256(video_path)

    phash_str: Optional[str] = None
    if frame_paths:
        try:
            phash_str = compute_phash(frame_paths[0])
        except Exception:
            phash_str = None

    fraud_flags: List[Dict[str, Any]] = []

    if source.lower() == "upload":
        fraud_flags.append(
            {
                "code": "UPLOAD_SOURCE",
                "severity": "medium",
                "detail": "Video uploaded as pre-recorded file instead of live camera stream.",
            }
        )

    # Query DB for duplicate video content in other attempts
    other_attempts = db.exec(select(Attempt).where(Attempt.id != attempt_id)).all()

    sha_dup_flagged = False
    phash_dup_flagged = False

    for other in other_attempts:
        if not sha_dup_flagged and other.video_sha256 and other.video_sha256 == file_sha256:
            fraud_flags.append(
                {
                    "code": "DUPLICATE_VIDEO_SHA256",
                    "severity": "high",
                    "detail": f"Exact binary duplicate of video from previous attempt {other.id}.",
                }
            )
            sha_dup_flagged = True

        if (
            not phash_dup_flagged
            and phash_str
            and other.video_phash
            and other.video_sha256 != file_sha256  # Avoid duplicate flag if already flagged by SHA
        ):
            try:
                dist = imagehash.hex_to_hash(phash_str) - imagehash.hex_to_hash(other.video_phash)
                if dist <= 4:
                    fraud_flags.append(
                        {
                            "code": "DUPLICATE_VIDEO_PHASH",
                            "severity": "high",
                            "detail": f"Visual perceptual duplicate of video from attempt {other.id} (Hamming distance: {dist}).",
                        }
                    )
                    phash_dup_flagged = True
            except Exception:
                pass

        if sha_dup_flagged and phash_dup_flagged:
            break

    return file_sha256, phash_str, fraud_flags
