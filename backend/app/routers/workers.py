import uuid
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlmodel import Session
from app.db import get_session
from app.models import Worker, utc_now
from app.schemas import APIError, APIResponse, WorkerCreate, WorkerResponse

router = APIRouter(tags=["workers"])


@router.post("/workers", response_model=APIResponse[WorkerResponse])
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
