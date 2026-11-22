import pytest
from app.ai.base import BaseAI
from app.ai.cache import AICache
from app.ai.fallback import FallbackAI
from app.ai.gemini import GeminiAI
from app.ai.mock import MockAI
from app.ai.utils import (
    AnalyzerResult,
    CoachResult,
    InterviewerResult,
    extract_json,
    validate_json,
)
from app.config import settings


# --- Tests for JSON Extraction & Validation ---
def test_extract_json_clean():
    raw = '{"name": "test", "value": 123}'
    parsed = extract_json(raw)
    assert parsed == {"name": "test", "value": 123}


def test_extract_json_code_fence():
    raw = """Here is the response:
```json
{
  "status": "success",
  "items": [1, 2, 3]
}
```
Hope that helps!"""
    parsed = extract_json(raw)
    assert parsed == {"status": "success", "items": [1, 2, 3]}


def test_extract_json_with_chatter():
    raw = 'Sure thing! The result is {"score": 90, "passed": true}. Let me know if you need anything else.'
    parsed = extract_json(raw)
    assert parsed == {"score": 90, "passed": True}


def test_extract_json_trailing_comma():
    raw = '{"name": "test", "items": [1, 2, ], }'
    parsed = extract_json(raw)
    assert parsed == {"name": "test", "items": [1, 2]}


def test_extract_json_empty_or_malformed():
    with pytest.raises(ValueError):
        extract_json("")

    with pytest.raises(ValueError):
        extract_json("This has no json at all whatsoever.")


def test_validate_analyzer_schema():
    raw = """
    {
      "steps": [
        {"id": "step_1", "verdict": "pass", "confidence": 0.95, "evidence_frames": [1, 2], "note": "All good"}
      ],
      "challenge_code_seen": true,
      "safety_items_seen": ["gloves"],
      "video_quality": {"rating": "good", "reason": "Clear video"}
    }
    """
    model = validate_json(raw, AnalyzerResult)
    assert len(model.steps) == 1
    assert model.steps[0].id == "step_1"
    assert model.steps[0].verdict == "pass"
    assert model.challenge_code_seen is True
    assert model.video_quality.rating == "good"


def test_validate_interviewer_schema():
    raw = """
    {
      "score": 85,
      "missing_points": ["grounding check"],
      "next": {"type": "followup", "text": "What about earthing?"}
    }
    """
    model = validate_json(raw, InterviewerResult)
    assert model.score == 85
    assert model.missing_points == ["grounding check"]
    assert model.next.type == "followup"


def test_validate_coach_schema():
    raw = """
    {
      "summary": "Solid demonstration.",
      "next_actions": ["Vouches", "Retest"],
      "unclear_steps_tips": [{"step_id": "step_2", "tip": "Show closer view"}]
    }
    """
    model = validate_json(raw, CoachResult)
    assert model.summary == "Solid demonstration."
    assert len(model.next_actions) == 2
    assert model.unclear_steps_tips[0].step_id == "step_2"


# --- Tests for MockAI ---
def test_mock_ai_analyzer():
    ai = MockAI()
    res = ai.generate_content("Please act as an analyzer for blueprint visual criteria")
    model = validate_json(res, AnalyzerResult)
    assert len(model.steps) >= 1
    assert model.challenge_code_seen is True
    assert model.video_quality.rating in ("good", "poor")


def test_mock_ai_interviewer():
    ai = MockAI()
    res = ai.generate_content("You are an interviewer asking scenario questions")
    model = validate_json(res, InterviewerResult)
    assert 0 <= model.score <= 100
    assert model.next.type in ("question", "followup", "done")


def test_mock_ai_coach():
    ai = MockAI()
    res = ai.generate_content("Provide coach explainer for credential result")
    model = validate_json(res, CoachResult)
    assert len(model.summary) > 0


def test_mock_ai_custom_responses():
    ai = MockAI(custom_responses=['{"custom": 1}', '{"custom": 2}'])
    assert ai.generate_content("first") == '{"custom": 1}'
    assert ai.generate_content("second") == '{"custom": 2}'
    # Once exhausted, defaults apply
    assert "mock_response" in ai.generate_content("third")


# --- Tests for AICache ---
def test_cache_save_and_retrieve(tmp_path):
    cache = AICache(cache_dir=tmp_path)
    prompt = "Test prompt"
    sys_inst = "System instruction"

    assert cache.get(prompt, system_instruction=sys_inst) is None

    cache.set(prompt, '{"result": "saved"}', system_instruction=sys_inst)
    retrieved = cache.get(prompt, system_instruction=sys_inst)
    assert retrieved == '{"result": "saved"}'


# --- Tests for FallbackAI ---
class FailingAI(BaseAI):
    def generate_content(self, prompt: str, system_instruction=None, image_paths=None) -> str:
        raise ConnectionError("Simulated network outage")


def test_fallback_ai_primary_success():
    primary = MockAI(custom_response='{"status": "primary"}')
    secondary = MockAI(custom_response='{"status": "secondary"}')
    fallback = FallbackAI(providers=[primary, secondary])

    result = fallback.generate_content("test")
    assert result == '{"status": "primary"}'
    assert len(primary.call_history) == 1
    assert len(secondary.call_history) == 0


def test_fallback_ai_primary_fails_secondary_succeeds():
    primary = FailingAI()
    secondary = MockAI(custom_response='{"status": "fallback_success"}')
    fallback = FallbackAI(providers=[primary, secondary])

    result = fallback.generate_content("test")
    assert result == '{"status": "fallback_success"}'
    assert len(secondary.call_history) == 1


def test_fallback_ai_all_fail():
    primary = FailingAI()
    secondary = FailingAI()
    fallback = FallbackAI(providers=[primary, secondary])

    with pytest.raises(RuntimeError) as exc_info:
        fallback.generate_content("test")
    assert "All AI providers in fallback chain failed" in str(exc_info.value)


# --- Tests for Gemini Safety & Configuration ---
def test_gemini_demo_mode_safety(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    gemini = GeminiAI(api_key="mock_key")
    with pytest.raises(RuntimeError) as exc_info:
        gemini.generate_content("test prompt")
    assert "disabled in DEMO_MODE" in str(exc_info.value)


def test_gemini_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    gemini = GeminiAI(api_key="")
    with pytest.raises(RuntimeError) as exc_info:
        gemini.generate_content("test prompt")
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)
