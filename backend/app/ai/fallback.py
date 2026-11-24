import logging
from typing import Optional

from app.ai.base import BaseAI
from app.ai.cache import AICache

logger = logging.getLogger(__name__)


class FallbackAI(BaseAI):
    """
    Fallback chain orchestrating multiple BaseAI providers in order of preference.
    Can be configured with an optional AICache for caching results.
    """

    def __init__(
        self,
        providers: list[BaseAI],
        cache: Optional[AICache] = None,
    ) -> None:
        if not providers:
            raise ValueError("FallbackAI requires at least one provider")
        self.providers = providers
        self.cache = cache

    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        image_paths: Optional[list[str]] = None,
    ) -> str:
        # Check cache if available
        if self.cache is not None:
            cached_response = self.cache.get(
                prompt=prompt,
                system_instruction=system_instruction,
                image_paths=image_paths,
            )
            if cached_response is not None:
                logger.debug("Cache hit in FallbackAI")
                return cached_response

        errors: list[str] = []
        from app.config import settings
        import os
        import sys
        is_demo = getattr(settings, "DEMO_MODE", False) or "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST") is not None

        for provider in self.providers:
            provider_name = provider.__class__.__name__
            # In DEMO_MODE or testing: skip network-dependent Gemini AI provider
            if is_demo and provider_name == "GeminiAI":
                logger.info("DEMO_MODE/test active: skipping external GeminiAI provider.")
                continue
            try:
                result = provider.generate_content(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    image_paths=image_paths,
                )
                # Save to cache if available
                if self.cache is not None:
                    self.cache.set(
                        prompt=prompt,
                        response=result,
                        system_instruction=system_instruction,
                        image_paths=image_paths,
                    )
                return result
            except Exception as exc:
                logger.warning(
                    f"AI provider '{provider_name}' failed with error: {exc}. Attempting next provider in fallback chain."
                )
                errors.append(f"{provider_name}: {str(exc)}")

        raise RuntimeError(f"All AI providers in fallback chain failed: {'; '.join(errors)}")
