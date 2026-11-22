from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIError(BaseModel):
    code: str
    message: str
    hint: Optional[str] = None


class APIResponse(BaseModel, Generic[T]):
    ok: bool
    data: Optional[T] = None
    error: Optional[APIError] = None
