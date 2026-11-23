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

        # In DEMO_MODE: immediately return mock response without attempting external network calls
        from app.config import settings
        if getattr(settings, "DEMO_MODE", False):
            logger.info("DEMO_MODE active: bypassing external network AI calls, selecting MockAI immediately.")
            from app.ai.mock import MockAI
            for provider in self.providers:
                if isinstance(provider, MockAI):
                    return provider.generate_content(prompt, system_instruction, image_paths)
            return MockAI().generate_content(prompt, system_instruction, image_paths)

        errors: list[str] = []
        for provider in self.providers:
            provider_name = provider.__class__.__name__
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
