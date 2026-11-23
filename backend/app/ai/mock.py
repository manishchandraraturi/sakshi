import json
import re
from typing import Optional
from app.ai.base import BaseAI


# Recognized trades and keywords from blueprints / demo scripts
RECOGNIZED_KEYWORDS = {
    # Electrician
    "electrician",
    "electrician_socket",
    "socket",
    "wire",
    "mcb",
    "voltage",
    "tester",
    "phase",
    "earth",
    "earthing",
    "terminal",
    "strip",
    # Plumber
    "plumber",
    "plumber_joint",
    "pipe",
    "pvc",
    "solvent",
    "joint",
    "bevel",
    "primer",
    "leak",
    # Mason
    "mason",
    "mason_wall",
    "brick",
    "mortar",
    "trowel",
    "spirit level",
    "plumb",
    "level",
    # Generic blueprint / prompt criteria
    "blueprint",
    "visual criteria",
    "evidence checker",
}


class MockAI(BaseAI):
    """
    Mock AI provider for testing, offline development, and fallback.
    Returns deterministic, schema-compliant responses matching 03_RULES.md.
    Does NOT rubber-stamp: returns 'unclear' / score 0 for unrecognized inputs
    or if text contains 'my pant is wet'.
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

        # Check for explicit failure / adversarial triggers
        is_adversarial = "my pant is wet" in combined_text or "unrecognized" in combined_text or "garbage" in combined_text

        # Check if matches recognized demo trades or blueprints
        is_recognized = any(k in combined_text for k in RECOGNIZED_KEYWORDS)

        # Prompt 1: Analyzer
        if any(k in combined_text for k in ["analyzer", "visual criteria", "evidence checker", "frames", "video_quality"]):
            extracted_ids = re.findall(r"step[\s_]?id:\s*([a-zA-Z0-9_-]+)", prompt, re.IGNORECASE)
            if not extracted_ids:
                extracted_ids = ["step_1", "step_2"]

            # If adversarial or unrecognized input, return "unclear" with 0 confidence
            if is_adversarial or not is_recognized:
                return json.dumps(
                    {
                        "steps": [
                            {
                                "id": sid,
                                "verdict": "unclear",
                                "confidence": 0.0,
                                "evidence_frames": [],
                                "note": f"Unrecognized input or criteria failed for {sid}.",
                            }
                            for sid in extracted_ids
                        ],
                        "challenge_code_seen": False,
                        "safety_items_seen": [],
                        "video_quality": {
                            "rating": "poor",
                            "reason": "Unrecognized activity or failed demonstration criteria.",
                        },
                    }
                )

            # Recognized pre-seeded demo input
            return json.dumps(
                {
                    "steps": [
                        {
                            "id": sid,
                            "verdict": "pass",
                            "confidence": 0.95,
                            "evidence_frames": [0, 1],
                            "note": f"Visual criteria verified for {sid}.",
                        }
                        for sid in extracted_ids
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
            if is_adversarial:
                return json.dumps(
                    {
                        "score": 0,
                        "missing_points": ["Irrelevant response: demonstration criteria not met"],
                        "next": {
                            "type": "done",
                            "text": "Your answer is off-topic or irrelevant. Score 0.",
                        },
                    }
                )

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
            if is_adversarial:
                return json.dumps(
                    {
                        "summary": "Assessment criteria not met due to unrecognized input.",
                        "next_actions": [
                            "Please review the assessment instructions and re-record.",
                        ],
                        "unclear_steps_tips": [
                            {"step_id": "step_1", "tip": "Demonstrate the required skill procedure clearly."}
                        ],
                    }
                )

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
