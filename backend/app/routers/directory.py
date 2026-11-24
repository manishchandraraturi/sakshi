"""
backend/app/routers/directory.py

Router for searching and discovering verified tradespeople.
Provides GET /api/directory?trade=&area=
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models import Credential, Vouch, Worker
from app.schemas import AnalyticsResponse, APIResponse, DirectoryItem

router = APIRouter(tags=["directory"])


@router.get("/directory/analytics", response_model=APIResponse[AnalyticsResponse])
def get_directory_analytics(db: Session = Depends(get_session)):
    """
    Returns aggregate workforce analytics for the hirer dashboard:
    - total_workers: count of registered workers in system
    - tier_distribution: breakdown by tier (tier_1, tier_2, tier_3)
    - trade_distribution: breakdown of verified credentials by trade
    - total_vouches: total recorded peer witness vouches
    """
    workers = db.exec(select(Worker)).all()
    total_workers = len(workers)

    credentials = db.exec(select(Credential).where(Credential.revoked == False)).all()
    vouches = db.exec(select(Vouch)).all()
    total_vouches = len(vouches)

    tier_dist = {"tier_1": 0, "tier_2": 0, "tier_3": 0}
    trade_dist: dict[str, int] = {}

    for cred in credentials:
        if cred.tier in (1, 2, 3):
            key = f"tier_{cred.tier}"
            tier_dist[key] = tier_dist.get(key, 0) + 1

        trade_name = "other"
        try:
            payload = json.loads(cred.payload_json)
            trade_name = payload.get("trade", "") or ""
        except Exception:
            trade_name = ""

        if not trade_name and cred.skill_id:
            trade_name = cred.skill_id.split("_")[0]

        trade_key = trade_name.strip().lower() if trade_name else "other"
        trade_dist[trade_key] = trade_dist.get(trade_key, 0) + 1

    return APIResponse[AnalyticsResponse](
        ok=True,
        data=AnalyticsResponse(
            total_workers=total_workers,
            tier_distribution=tier_dist,
            trade_distribution=trade_dist,
            total_vouches=total_vouches,
        ),
        error=None,
    )


@router.get("/directory", response_model=APIResponse[List[DirectoryItem]])
def list_directory(
    trade: Optional[str] = Query(None, description="Filter by trade (e.g. Electrician, Plumber, Mason)"),
    area: Optional[str] = Query(None, description="Filter by area / location"),
    db: Session = Depends(get_session),
):
    """
    Returns verified workers with active Ed25519 digital credentials,
    optionally filtered by trade and area.
    """
    statement = (
        select(Credential, Worker)
        .join(Worker, Credential.worker_id == Worker.id)
        .where(Credential.revoked == False)
        .order_by(Credential.tier.desc(), Credential.trust_score.desc())
    )
    results = db.exec(statement).all()

    items: List[DirectoryItem] = []
    trade_filter = trade.strip().lower() if trade else None
    area_filter = area.strip().lower() if area else None

    for cred, worker in results:
        # Extract metadata from canonical payload_json
        try:
            payload = json.loads(cred.payload_json)
        except Exception:
            payload = {}

        w_name = payload.get("worker_name", worker.name)
        w_trade = payload.get("trade", "")
        w_skill = payload.get("skill", cred.skill_id)
        w_area = payload.get("area", worker.area)

        # Apply trade filter
        if trade_filter and (trade_filter not in w_trade.lower() and trade_filter not in w_skill.lower()):
            continue

        # Apply area filter
        if area_filter and (area_filter not in w_area.lower()):
            continue

        items.append(
            DirectoryItem(
                credential_id=cred.id,
                name=w_name,
                trade=w_trade,
                skill=w_skill,
                tier=cred.tier,
                trust_score=cred.trust_score,
                area=w_area,
                issued_at=cred.issued_at.isoformat() if cred.issued_at else None,
            )
        )

    return APIResponse[List[DirectoryItem]](ok=True, data=items, error=None)
