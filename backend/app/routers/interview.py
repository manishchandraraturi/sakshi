from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.agent.loop import run_interview_step
from app.db import get_session
from app.models import Attempt
from app.schemas import APIError, APIResponse, InterviewRequest, InterviewResponse

router = APIRouter(tags=["interview"])


@router.post(
    "/attempts/{attempt_id}/interview/next",
    response_model=APIResponse[InterviewResponse],
)
def next_interview_step(
    attempt_id: str,
    payload: InterviewRequest,
    db: Session = Depends(get_session),
):
    """
    Step through the AI interview scenario questions for an active attempt.
    """
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
                    hint="Please verify the attempt ID.",
                ),
            ).model_dump(),
        )

    if attempt.status != "interviewing":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="INVALID_ATTEMPT_STATUS",
                    message=f"Attempt is in status '{attempt.status}', expected 'interviewing'.",
                    hint="The interview for this attempt may have already finished.",
                ),
            ).model_dump(),
        )

    response_data = run_interview_step(attempt=attempt, answer=payload.answer, db=db)

    return APIResponse[InterviewResponse](
        ok=True,
        data=response_data,
        error=None,
    )
