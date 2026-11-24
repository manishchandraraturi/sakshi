"""
backend/app/routers/witness.py

API router for witness invitation link creation, witness review page data,
and vouch submission with deterministic weighting and anti-fraud checks.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.config import settings
from app.db import get_session
from app.schemas import (
    APIError,
    APIResponse,
    VouchCreate,
    VouchResponse,
    WitnessInviteCreate,
    WitnessInviteResponse,
    WitnessPageData,
)
from app.services import witness_service
from app.utils.rate_limiter import witness_vouch_limiter

router = APIRouter(tags=["witnesses"])


@router.post(
    "/attempts/{attempt_id}/witnesses",
    response_model=APIResponse[List[WitnessInviteResponse]],
)
def create_witness_invites(
    attempt_id: str,
    body: Optional[WitnessInviteCreate] = None,
    db: Session = Depends(get_session),
):
    """
    Generate one-time witness invite links for a candidate's skill attempt.
    """
    count = body.count if body and body.count else 3
    base_url = settings.PUBLIC_BASE_URL

    try:
        invites = witness_service.create_witness_invites(
            attempt_id=attempt_id,
            count=count,
            db=db,
            base_url=base_url,
        )
        return APIResponse[List[WitnessInviteResponse]](
            ok=True,
            data=[WitnessInviteResponse(**inv) for inv in invites],
            error=None,
        )
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
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
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="INVITE_GENERATION_FAILED",
                    message=err_msg,
                ),
            ).model_dump(),
        )


@router.get(
    "/w/{token}",
    response_model=APIResponse[WitnessPageData],
)
def get_witness_page(
    token: str,
    db: Session = Depends(get_session),
):
    """
    Retrieve witness review page data (candidate first name, skill, checklist, clip URL).
    Rejects tokens that do not exist or have already been consumed.
    """
    try:
        data = witness_service.get_witness_page_data(token=token, db=db)
        return APIResponse[WitnessPageData](
            ok=True,
            data=WitnessPageData(**data),
            error=None,
        )
    except ValueError as e:
        code = str(e)
        if code == "INVITE_NOT_FOUND":
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIResponse[None](
                    ok=False,
                    data=None,
                    error=APIError(
                        code="INVITE_NOT_FOUND",
                        message=f"Witness invite token '{token}' was not found.",
                        hint="Check the invite link or ask the candidate for a new one.",
                    ),
                ).model_dump(),
            )
        elif code == "INVITE_ALREADY_USED":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=APIResponse[None](
                    ok=False,
                    data=None,
                    error=APIError(
                        code="INVITE_ALREADY_USED",
                        message="This witness invite link has already been used.",
                        hint="Witness invite links are one-time use only.",
                    ),
                ).model_dump(),
            )
        elif code == "ATTEMPT_NOT_FOUND":
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIResponse[None](
                    ok=False,
                    data=None,
                    error=APIError(
                        code="ATTEMPT_NOT_FOUND",
                        message="The associated skill attempt was not found.",
                    ),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="INVALID_INVITE",
                    message=str(e),
                ),
            ).model_dump(),
        )


@router.post(
    "/w/{token}/vouch",
    response_model=APIResponse[VouchResponse],
    dependencies=[Depends(witness_vouch_limiter.check)],
)
def submit_vouch(
    token: str,
    body: VouchCreate,
    db: Session = Depends(get_session),
):
    """
    Submit a witness vouch with role, relationship details, and verdict.
    Calculates deterministic trust weight and marks the invite token as used.
    """
    try:
        vouch = witness_service.submit_vouch(
            token=token,
            vouch_data=body,
            db=db,
        )
        return APIResponse[VouchResponse](
            ok=True,
            data=VouchResponse(
                vouch_id=vouch.id,
                weight=vouch.weight,
                attempt_id=vouch.attempt_id,
                status="recorded",
            ),
            error=None,
        )
    except ValueError as e:
        code = str(e)
        if code == "INVITE_NOT_FOUND":
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIResponse[None](
                    ok=False,
                    data=None,
                    error=APIError(
                        code="INVITE_NOT_FOUND",
                        message=f"Witness invite token '{token}' was not found.",
                    ),
                ).model_dump(),
            )
        elif code == "INVITE_ALREADY_USED":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=APIResponse[None](
                    ok=False,
                    data=None,
                    error=APIError(
                        code="INVITE_ALREADY_USED",
                        message="This witness invite link has already been used.",
                        hint="Witness invite links are one-time use only.",
                    ),
                ).model_dump(),
            )
        elif code == "ATTEMPT_NOT_FOUND":
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=APIResponse[None](
                    ok=False,
                    data=None,
                    error=APIError(
                        code="ATTEMPT_NOT_FOUND",
                        message="The associated skill attempt was not found.",
                    ),
                ).model_dump(),
            )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=APIResponse[None](
                ok=False,
                data=None,
                error=APIError(
                    code="VOUCH_SUBMISSION_FAILED",
                    message=str(e),
                ),
            ).model_dump(),
        )
