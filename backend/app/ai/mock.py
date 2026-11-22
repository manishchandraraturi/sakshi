import json
from typing import Optional
from app.ai.base import BaseAI


class MockAI(BaseAI):
    """
    Mock AI provider for testing, offline development, and fallback.
    Returns deterministic, schema-compliant responses matching 03_RULES.md.
    """

    def __init__(
        self,
        custom_response: Optional[str] = None,
        custom_responses: Optional[list[str]] = None,
    ) -> None:
        self.custom_response = custom_response
        self.custom_responses = list(custom_responses) if custom_responses else []
        self.call_history: list[dict] = []

    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        image_paths: Optional[list[str]] = None,
    ) -> str:
        self.call_history.append(
            {
                "prompt": prompt,
                "system_instruction": system_instruction,
                "image_paths": image_paths,
            }
        )

        if self.custom_responses:
            return self.custom_responses.pop(0)

        if self.custom_response is not None:
            return self.custom_response

        combined_text = f"{system_instruction or ''} {prompt}".lower()

        # Prompt 1: Analyzer
        if any(k in combined_text for k in ["analyzer", "visual criteria", "evidence checker", "frames", "video_quality"]):
            return json.dumps(
                {
                    "steps": [
                        {
                            "id": "step_1",
                            "verdict": "pass",
                            "confidence": 0.95,
                            "evidence_frames": [0, 1],
                            "note": "Work area prepared and correct tools observed.",
                        },
                        {
                            "id": "step_2",
                            "verdict": "pass",
                            "confidence": 0.92,
                            "evidence_frames": [2, 3],
                            "note": "Required step technique accurately executed.",
                        },
                    ],
                    "challenge_code_seen": True,
                    "safety_items_seen": ["safety_gloves", "safety_glasses"],
                    "video_quality": {
                        "rating": "good",
                        "reason": "Clear illumination and focused camera angle.",
                    },
                }
            )

        # Prompt 2: Interviewer
        if any(k in combined_text for k in ["interviewer", "interview", "scenario", "question", "missing_points"]):
            return json.dumps(
                {
                    "score": 85,
                    "missing_points": [],
                    "next": {
                        "type": "question",
                        "text": "What steps do you take to verify safety before beginning work?",
                    },
                }
            )

        # Prompt 3: Coach / Explainer
        if any(k in combined_text for k in ["coach", "explainer", "credential result", "unclear_steps_tips"]):
            return json.dumps(
                {
                    "summary": "Demonstrated solid technical execution in your practical assessment.",
                    "next_actions": [
                        "Request 2 peer witness verifications to advance to Tier 2",
                        "Review tool handling best practices",
                    ],
                    "unclear_steps_tips": [],
                }
            )

        # Generic default mock response
        return json.dumps({"ok": True, "message": "mock_response"})
