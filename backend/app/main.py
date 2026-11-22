from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel

from app.config import settings
from app.db import engine
from app.routers import attempts, interview, skills, video, workers
from app.schemas import APIError, APIResponse
import app.models  # noqa: F401 - ensure all tables are registered in SQLModel.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    title="SAKSHI API",
    description="Skills, witnessed. Micro-credentialing platform.",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    error_payload = APIResponse[None](
        ok=False,
        data=None,
        error=APIError(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred.",
            hint=str(exc) if settings.DEMO_MODE else None,
        ),
    )
    return JSONResponse(status_code=500, content=error_payload.model_dump())


# Include API routers
app.include_router(skills.router, prefix="/api")
app.include_router(workers.router, prefix="/api")
app.include_router(attempts.router, prefix="/api")
app.include_router(interview.router, prefix="/api")
app.include_router(video.router, prefix="/api")


@app.get("/api/health", response_model=APIResponse[dict])
async def health_check() -> APIResponse[dict]:
    return APIResponse[dict](
        ok=True,
        data={
            "status": "healthy",
            "demo_mode": settings.DEMO_MODE,
        },
        error=None,
    )
