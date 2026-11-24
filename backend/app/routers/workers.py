import json
from pathlib import Path
import shutil
import uuid
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from app.db import get_session
from app.models import Attempt, AuditLog, Credential, Worker, utc_now
from app.schemas import APIError, APIResponse, WorkerCreate, WorkerResponse
from app.utils.rate_limiter import worker_signup_limiter

router = APIRouter(tags=["workers"])


@router.post(
    "/workers",
    response_model=APIResponse[WorkerResponse],
    dependencies=[Depends(worker_signup_limiter.check)],
)
def create_worker(
    payload: WorkerCreate,
    db: Session = Depends(get_session),
):
    if not payload.consent:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="CONSENT_REQUIRED",
                    message="Worker consent is required.",
                    hint="Set consent=True to proceed.",
                ),
            ).model_dump(),
        )

    worker_id = str(uuid.uuid4())
    token = str(uuid.uuid4())
    now = utc_now()

    worker = Worker(
        id=worker_id,
        name=payload.name,
        language=payload.language,
        area=payload.area,
        phone_optional=payload.phone_optional,
        device_fp=payload.device_fp,
        token=token,
        consent_at=now,
        created_at=now,
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)

    return APIResponse[WorkerResponse](
        ok=True,
        data=WorkerResponse(worker_id=worker.id, token=worker.token),
        error=None,
    )


@router.delete("/workers/{worker_id}/data", response_model=APIResponse[dict])
def delete_worker_data(
    worker_id: str,
    request: Request,
    db: Session = Depends(get_session),
):
    """
    Deletes all media files (video & frames) associated with worker's attempts,
    revokes all credentials issued to the worker, and anonymizes worker identity.
    Requires Bearer token authentication.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="UNAUTHORIZED",
                    message="Missing or invalid Authorization header.",
                    hint="Provide a valid Bearer token.",
                ),
            ).model_dump(),
        )

    token = auth_header.split(" ", 1)[1].strip()
    worker = db.exec(select(Worker).where(Worker.id == worker_id)).first()
    if not worker:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="WORKER_NOT_FOUND",
                    message=f"Worker '{worker_id}' not found.",
                ),
            ).model_dump(),
        )

    if worker.token != token:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="FORBIDDEN",
                    message="Token does not match this worker.",
                ),
            ).model_dump(),
        )

    # 1. Delete video files and frames from disk for all attempts by this worker
    attempts = db.exec(select(Attempt).where(Attempt.worker_id == worker.id)).all()
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    videos_dir = data_dir / "videos"
    frames_dir = data_dir / "frames"

    for attempt in attempts:
        if attempt.video_path:
            p = Path(attempt.video_path)
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass
        for cand in [
            videos_dir / f"{attempt.id}.mp4",
            videos_dir / f"{attempt.id}.webm",
            videos_dir / f"{attempt.id}_rerecord.mp4",
            videos_dir / f"{attempt.id}_rerecord.webm",
        ]:
            if cand.exists():
                try:
                    cand.unlink()
                except Exception:
                    pass

        for f_dir in [
            frames_dir / attempt.id,
            frames_dir / f"{attempt.id}_rerecord",
        ]:
            if f_dir.exists() and f_dir.is_dir():
                try:
                    shutil.rmtree(f_dir)
                except Exception:
                    pass

        attempt.video_path = None
        db.add(attempt)

    # 2. Mark all credentials as revoked
    credentials = db.exec(select(Credential).where(Credential.worker_id == worker.id)).all()
    for cred in credentials:
        cred.revoked = True
        db.add(cred)

    # 3. Anonymize worker record
    worker.name = "Deleted Worker"
    worker.phone_optional = None
    db.add(worker)

    # 4. Log audit action
    audit = AuditLog(
        actor=worker.id,
        action="delete_my_data",
        ref_id=worker.id,
        detail_json=json.dumps({
            "revoked_credentials": len(credentials),
            "deleted_attempts": len(attempts),
        }),
    )
    db.add(audit)
    db.commit()

    return APIResponse[dict](
        ok=True,
        data={
            "message": "Worker data and media files deleted successfully, credentials revoked.",
            "worker_id": worker.id,
            "revoked_credentials": len(credentials),
        },
        error=None,
    )
