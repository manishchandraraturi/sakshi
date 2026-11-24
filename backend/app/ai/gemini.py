import logging
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.ai.base import BaseAI
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiAI(BaseAI):
    """
    Google Gemini provider using official google-genai SDK.
    Includes tenacity exponential backoff retries and DEMO_MODE safety checks.
    Seamlessly delegates to FallbackAI on quota, connection, or execution errors.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if settings.DEMO_MODE:
            raise RuntimeError("Gemini live calls disabled in DEMO_MODE")
        key_to_use = self.api_key if self.api_key is not None else settings.GEMINI_API_KEY
        if not key_to_use or key_to_use.strip() == "" or key_to_use == "your_actual_api_key_here":
            raise RuntimeError("GEMINI_API_KEY is not configured")
        if self._client is None:
            try:
                self._client = genai.Client(api_key=key_to_use)
            except Exception as e:
                logger.error(f"Failed to initialize google-genai Client: {e}")
                raise RuntimeError(f"Failed to initialize Gemini client: {e}") from e
        return self._client

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    def _execute_request(self, contents: list, config: types.GenerateContentConfig) -> str:
        client = self._get_client()
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            if not response or not response.text:
                raise ValueError("Empty or invalid response from Gemini API")
            return response.text
        except Exception as err:
            logger.warning(
                f"Gemini API request failed for model '{self.model_name}': {err}"
            )
            raise

    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        image_paths: Optional[list[str]] = None,
    ) -> str:
        try:
            contents: list = []

            if image_paths:
                for path_str in image_paths:
                    p = Path(path_str)
                    if p.exists():
                        with open(p, "rb") as f:
                            data = f.read()
                        mime_type = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
                        contents.append(types.Part.from_bytes(data=data, mime_type=mime_type))
                    else:
                        logger.warning(f"Image path not found: {path_str}")

            contents.append(prompt)

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            )

            return self._execute_request(contents, config)
        except Exception as exc:
            logger.error(
                f"GeminiAI invocation failed ({self.model_name}): {exc}. "
                "Raising exception for FallbackAI to route to MockAI."
            )
            raise
