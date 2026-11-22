from typing import List
from fastapi import APIRouter
from app.blueprints.loader import load_blueprint
from app.schemas import APIResponse, SkillStepSummary, SkillSummary, TradeSummary

router = APIRouter(tags=["skills"])

DEFAULT_SKILLS = ["electrician_socket", "plumber_joint", "mason_wall"]


@router.get("/skills", response_model=APIResponse[List[TradeSummary]])
def get_skills() -> APIResponse[List[TradeSummary]]:
    trades_map: dict[str, List[SkillSummary]] = {}

    for sid in DEFAULT_SKILLS:
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

    result = [
        TradeSummary(trade=trade, skills=skills)
        for trade, skills in trades_map.items()
    ]
    return APIResponse(ok=True, data=result, error=None)
