import json
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.agent.review import run_review_decision
from app.config import settings
from app.db import engine, get_session
from app.models import Attempt, utc_now
from app.schemas import APIError, APIResponse
from app.video.frames import extract_frames
from app.video.fraud import detect_fraud
from app.video.meta import extract_metadata

router = APIRouter(tags=["video"])


def process_video_analysis_task(attempt_id: str) -> None:
    """
    Background worker task to run AI video frame analysis and review decision.
    Executes in a dedicated DB session to avoid session detachment after HTTP response ends.
    Uses app dependency override if registered (for isolated test DB) or default get_session.
    """
    from app.main import app
    session_generator = app.dependency_overrides.get(get_session, get_session)
    for session in session_generator():
        attempt = session.exec(select(Attempt).where(Attempt.id == attempt_id)).first()
        if attempt:
            run_review_decision(attempt=attempt, db=session)
        break


@router.post(
    "/attempts/{attempt_id}/video",
    response_model=APIResponse[dict],
)
async def upload_attempt_video(
    attempt_id: str,
    background_tasks: BackgroundTasks,
    source: str = Query("live", description="'live' or 'upload'"),
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
):
    """
    Accepts candidate practical demonstration video (live recording or upload).
    Validates size and duration bounds, extracts up to 12 frames, computes hashes,
    checks for duplicates (fraud detection), and updates attempt status to 'analyzing'.
    """
    # 1. Fetch and validate attempt
    attempt = db.exec(select(Attempt).where(Attempt.id == attempt_id)).first()
    if not attempt:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="ATTEMPT_NOT_FOUND",
                    message=f"Attempt '{attempt_id}' not found.",
                ),
            ).model_dump(),
        )

    valid_statuses = ("awaiting_video", "interviewing", "created", "needs_rerecord")
    if attempt.status not in valid_statuses:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="INVALID_ATTEMPT_STATUS",
                    message=f"Attempt is currently in '{attempt.status}' status, cannot upload video.",
                    hint="Video upload is only allowed when awaiting video recording.",
                ),
            ).model_dump(),
        )

    # 2. Setup directories
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    videos_dir = data_dir / "videos"
    frames_dir = data_dir / "frames" / attempt_id
    videos_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    dest_file = videos_dir / f"{attempt_id}.mp4"

    # 3. Read content and enforce size limits
    max_bytes = settings.MAX_VIDEO_MB * 1024 * 1024
    total_bytes = 0

    try:
        with open(dest_file, "wb") as f:
            while chunk := await file.read(65536):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    f.close()
                    if dest_file.exists():
                        dest_file.unlink()
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content=APIResponse[None](
                            ok=False,
                            data=None,
                            error=APIError(
                                code="MAX_SIZE_EXCEEDED",
                                message=f"Video file exceeds maximum allowed size of {settings.MAX_VIDEO_MB}MB.",
                            ),
                        ).model_dump(),
                    )
                f.write(chunk)

        if total_bytes == 0:
            if dest_file.exists():
                dest_file.unlink()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=APIResponse[None](
                    ok=False,
                    data=None,
                    error=APIError(
                        code="EMPTY_VIDEO",
                        message="Uploaded video file is empty.",
                    ),
                ).model_dump(),
            )

        # 4. Extract and check metadata
        try:
            meta = extract_metadata(dest_file)
        except Exception as e:
            if dest_file.exists():
                dest_file.unlink()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=APIResponse[None](
                    ok=False,
                    data=None,
                    error=APIError(
                        code="INVALID_VIDEO",
                        message="Could not read video metadata. Please upload a valid video file.",
                        hint=str(e),
                    ),
                ).model_dump(),
            )

        duration = meta["duration"]
        if duration <= settings.MIN_VIDEO_SECONDS:
            if dest_file.exists():
                dest_file.unlink()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=APIResponse[None](
                    ok=False,
                    data=None,
                    error=APIError(
                        code="VIDEO_TOO_SHORT",
                        message=f"Video duration ({duration}s) is too short. Minimum duration is {settings.MIN_VIDEO_SECONDS + 1} seconds.",
                    ),
                ).model_dump(),
            )

        if duration > settings.MAX_VIDEO_SECONDS:
            if dest_file.exists():
                dest_file.unlink()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=APIResponse[None](
                    ok=False,
                    data=None,
                    error=APIError(
                        code="VIDEO_TOO_LONG",
                        message=f"Video duration ({duration}s) exceeds maximum of {settings.MAX_VIDEO_SECONDS} seconds.",
                    ),
                ).model_dump(),
            )

        # 5. Extract frames
        try:
            frame_paths = extract_frames(dest_file, frames_dir, max_frames=12, max_dimension=768)
        except Exception as e:
            if dest_file.exists():
                dest_file.unlink()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=APIResponse[None](
                    ok=False,
                    data=None,
                    error=APIError(
                        code="FRAME_EXTRACTION_FAILED",
                        message="Could not extract frames from video. Please record again.",
                        hint=str(e),
                    ),
                ).model_dump(),
            )

        # 6. Fraud detection & duplicate checks
        file_sha256, phash_str, fraud_flags = detect_fraud(
            video_path=dest_file,
            frame_paths=frame_paths,
            attempt_id=attempt_id,
            source=source,
            db=db,
        )

        # 7. Update attempt record
        attempt.status = "analyzing"
        attempt.video_path = str(dest_file).replace("\\", "/")
        attempt.video_sha256 = file_sha256
        attempt.video_phash = phash_str
        attempt.video_meta_json = json.dumps(meta)
        attempt.fraud_flags_json = json.dumps(fraud_flags)
        attempt.updated_at = utc_now()

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        # 8. Schedule asynchronous AI analysis via FastAPI BackgroundTasks
        background_tasks.add_task(process_video_analysis_task, attempt.id)

        return APIResponse[dict](
            ok=True,
            data={
                "status": "analyzing",
                "frames_count": len(frame_paths),
                "fraud_flags": fraud_flags,
            },
            error=None,
        )

    finally:
        await file.close()
