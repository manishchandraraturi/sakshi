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
from app.models import Credential, Worker
from app.schemas import APIResponse, DirectoryItem

router = APIRouter(tags=["directory"])


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
