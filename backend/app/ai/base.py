from abc import ABC, abstractmethod
from typing import Optional


class BaseAI(ABC):
    """Abstract base class for all AI model providers."""

    @abstractmethod
    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        image_paths: Optional[list[str]] = None,
    ) -> str:
        """
        Generate text content given a user prompt, optional system instruction,
        and optional list of file paths to images.
        """
        pass
