import json
import re
from typing import Any, Literal, Optional, Type, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


# --- Prompt 1: Analyzer Models ---
class AnalyzerStep(BaseModel):
    id: str
    verdict: Literal["pass", "fail", "unclear"]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_frames: list[int] = Field(default_factory=list)
    note: str = ""


class VideoQuality(BaseModel):
    rating: Literal["good", "poor"]
    reason: str = ""


class AnalyzerResult(BaseModel):
    steps: list[AnalyzerStep]
    challenge_code_seen: bool
    safety_items_seen: list[str] = Field(default_factory=list)
    video_quality: VideoQuality


# --- Prompt 2: Interviewer Models ---
class InterviewNext(BaseModel):
    type: Literal["question", "followup", "done"]
    text: str = ""


class InterviewerResult(BaseModel):
    score: int = Field(ge=0, le=100)
    missing_points: list[str] = Field(default_factory=list)
    next: InterviewNext


# --- Prompt 3: Coach / Explainer Models ---
class UnclearStepTip(BaseModel):
    step_id: str
    tip: str


class CoachResult(BaseModel):
    summary: str
    next_actions: list[str] = Field(default_factory=list)
    unclear_steps_tips: list[UnclearStepTip] = Field(default_factory=list)


# --- JSON Extraction and Validation ---
def extract_json(text: str) -> dict[str, Any] | list[Any]:
    """
    Extract and parse JSON from raw LLM output.
    Handles markdown code blocks, conversational prelude/epilogue,
    and common syntax quirks such as trailing commas.
    """
    if not text or not text.strip():
        raise ValueError("Cannot extract JSON from empty text")

    clean = text.strip()

    # 1. Check for markdown code fences (```json ... ``` or ``` ... ```)
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean, re.IGNORECASE)
    if code_block_match:
        clean = code_block_match.group(1).strip()

    # 2. Attempt direct JSON parsing
    try:
        parsed = json.loads(clean)
        if isinstance(parsed, (dict, list)):
            return parsed
    except json.JSONDecodeError:
        pass

    # 3. Locate outer JSON boundaries ({...} or [...])
    start_obj = clean.find("{")
    end_obj = clean.rfind("}")

    start_arr = clean.find("[")
    end_arr = clean.rfind("]")

    candidate: Optional[str] = None
    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        if start_arr != -1 and start_arr < start_obj and end_arr > end_obj:
            candidate = clean[start_arr : end_arr + 1]
        else:
            candidate = clean[start_obj : end_obj + 1]
    elif start_arr != -1 and end_arr != -1 and end_arr > start_arr:
        candidate = clean[start_arr : end_arr + 1]

    if candidate:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, (dict, list)):
                return parsed
        except json.JSONDecodeError:
            # 4. Attempt repair: remove trailing commas before closing braces/brackets
            repaired = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                parsed = json.loads(repaired)
                if isinstance(parsed, (dict, list)):
                    return parsed
            except json.JSONDecodeError:
                pass

    snippet = (clean[:120] + "...") if len(clean) > 120 else clean
    raise ValueError(f"Could not parse valid JSON from text: {snippet}")


def validate_json(raw: str | dict[str, Any] | list[Any], model_cls: Type[T]) -> T:
    """
    Extracts JSON if input is a string, then validates against a Pydantic model.
    """
    if isinstance(raw, str):
        data = extract_json(raw)
    else:
        data = raw

    return model_cls.model_validate(data)
