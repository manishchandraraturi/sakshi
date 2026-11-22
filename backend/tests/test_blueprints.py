import pytest
from pydantic import ValidationError
from app.blueprints.loader import Blueprint, load_blueprint


def test_load_electrician_blueprint():
    bp = load_blueprint("electrician_socket")
    assert bp.skill_id == "electrician_socket"
    assert bp.trade == "Electrician"
    assert len(bp.steps) >= 4
    assert len(bp.scenario_questions) >= 3
    assert len(bp.safety_items) >= 1
    assert any(step.safety_critical for step in bp.steps)


def test_load_all_blueprints():
    for skill_id in ["electrician_socket", "plumber_joint", "mason_wall"]:
        bp = load_blueprint(skill_id)
        assert bp.skill_id == skill_id
        assert len(bp.steps) >= 4
        assert len(bp.scenario_questions) >= 3


def test_malformed_blueprint_validation_error():
    # Missing required 'steps' field
    malformed_json_missing_steps = """
    {
        "skill_id": "test_skill",
        "trade": "Tester",
        "name": "Testing skill"
    }
    """
    with pytest.raises(ValidationError):
        Blueprint.model_validate_json(malformed_json_missing_steps)

    # Missing required 'visual_criteria' in step
    malformed_json_missing_visual_criteria = """
    {
        "skill_id": "test_skill",
        "trade": "Tester",
        "name": "Testing skill",
        "steps": [
            {
                "id": "step_1",
                "title": "Incomplete step"
            }
        ]
    }
    """
    with pytest.raises(ValidationError):
        Blueprint.model_validate_json(malformed_json_missing_visual_criteria)


def test_nonexistent_blueprint_raises_value_error():
    with pytest.raises(ValueError):
        load_blueprint("nonexistent_skill")
