from typing import List
from fastapi import APIRouter
from app.blueprints.loader import get_available_skill_ids, load_blueprint
from app.schemas import APIResponse, SkillStepSummary, SkillSummary, TradeSummary

router = APIRouter(tags=["skills"])


@router.get("/skills", response_model=APIResponse[List[TradeSummary]])
def get_skills() -> APIResponse[List[TradeSummary]]:
    trades_map: dict[str, List[SkillSummary]] = {}

    all_skill_ids = get_available_skill_ids()
    priority_order = ["electrician_socket", "plumber_joint", "mason_wall", "welder_pipe", "carpenter_joint"]
    sorted_sids = sorted(all_skill_ids, key=lambda x: priority_order.index(x) if x in priority_order else 999)

    for sid in sorted_sids:
        try:
            bp = load_blueprint(sid)
            steps_summary = [
                SkillStepSummary(id=s.id, title=s.title, critical=s.critical)
                for s in bp.steps
            ]
            skill_summary = SkillSummary(
                id=bp.skill_id,
                skill_id=bp.skill_id,
                name=bp.name,
                steps=steps_summary,
            )
            if bp.trade not in trades_map:
                trades_map[bp.trade] = []
            trades_map[bp.trade].append(skill_summary)
        except Exception:
            continue

    result = [
        TradeSummary(trade=trade, skills=skills)
        for trade, skills in trades_map.items()
    ]
    return APIResponse(ok=True, data=result, error=None)
