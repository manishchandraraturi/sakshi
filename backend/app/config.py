import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if it exists in backend/ or root
backend_env = Path(__file__).resolve().parent.parent / ".env"
root_env = Path(__file__).resolve().parent.parent.parent / ".env"
if backend_env.exists():
    load_dotenv(dotenv_path=backend_env)
elif root_env.exists():
    load_dotenv(dotenv_path=root_env)
else:
    load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        self.FALLBACK_AI_KEY: str = os.getenv("FALLBACK_AI_KEY", "")
        self.AI_MODEL_NAME: str = os.getenv("AI_MODEL_NAME", "gemini-2.5-flash")
        self.DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")
        self.MAX_VIDEO_MB: int = int(os.getenv("MAX_VIDEO_MB", "50"))
        self.MAX_VIDEO_SECONDS: int = int(os.getenv("MAX_VIDEO_SECONDS", "120"))
        self.MIN_VIDEO_SECONDS: int = int(os.getenv("MIN_VIDEO_SECONDS", "3"))
        self.CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        self.PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:5173")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
