import hashlib
import json
from pathlib import Path
from typing import Optional


class AICache:
    """
    Disk-based cache for AI model responses keyed by input hash (SHA-256).
    Enables zero-cost repeatable runs and offline testing during DEMO_MODE.
    """

    def __init__(self, cache_dir: Optional[Path | str] = None) -> None:
        if cache_dir is not None:
            self.cache_dir = Path(cache_dir)
        else:
            # Default to backend/data/ai_cache
            self.cache_dir = Path(__file__).resolve().parent.parent.parent / "data" / "ai_cache"

    def _compute_key(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        image_paths: Optional[list[str]] = None,
    ) -> str:
        images_str = ",".join(sorted(image_paths or []))
        raw_key = f"{system_instruction or ''}|||{prompt}|||{images_str}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        image_paths: Optional[list[str]] = None,
    ) -> Optional[str]:
        cache_key = self._compute_key(prompt, system_instruction, image_paths)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("response")
        except Exception:
            return None

    def set(
        self,
        prompt: str,
        response: str,
        system_instruction: Optional[str] = None,
        image_paths: Optional[list[str]] = None,
    ) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_key = self._compute_key(prompt, system_instruction, image_paths)
        cache_file = self.cache_dir / f"{cache_key}.json"

        payload = {
            "key": cache_key,
            "prompt": prompt,
            "system_instruction": system_instruction,
            "image_paths": image_paths or [],
            "response": response,
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
