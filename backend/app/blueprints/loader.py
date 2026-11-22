import json
from pathlib import Path
from typing import List
from pydantic import BaseModel, ValidationError

BLUEPRINTS_DIR = Path(__file__).resolve().parent


class Step(BaseModel):
    id: str
    title: str
    visual_criteria: str
    critical: bool = False
    safety_critical: bool = False


class ScenarioQuestion(BaseModel):
    id: str
    text: str
    expected_points: List[str]


class Blueprint(BaseModel):
    skill_id: str
    trade: str
    name: str
    steps: List[Step]
    safety_items: List[str] = []
    scenario_questions: List[ScenarioQuestion] = []
    common_mistakes: List[str] = []


def load_blueprint(skill_id: str) -> Blueprint:
    file_path = BLUEPRINTS_DIR / f"{skill_id}.json"
    if not file_path.exists():
        raise ValueError(f"Blueprint '{skill_id}' not found at {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Blueprint.model_validate_json(content)
    except (ValidationError, json.JSONDecodeError) as e:
        raise ValueError(f"Malformed blueprint JSON for '{skill_id}': {e}") from e


def get_available_skill_ids() -> List[str]:
    return [p.stem for p in BLUEPRINTS_DIR.glob("*.json")]
