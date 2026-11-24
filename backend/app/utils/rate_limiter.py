import time
from typing import Callable, Dict, List
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.schemas import APIError, APIResponse


class RateLimitExceeded(Exception):
    """Exception raised when an IP exceeds rate limit bounds."""

    def __init__(
        self,
        detail: str = "Too many requests. Please try again later.",
        retry_after: int = 60,
    ) -> None:
        self.detail = detail
        self.retry_after = retry_after
        super().__init__(detail)


class InMemoryRateLimiter:
    """
    Thread-safe, sliding-window in-memory rate limiter tracking timestamps per client IP.
    """

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.history: Dict[str, List[float]] = {}

    def get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "127.0.0.1"

    def check(self, request: Request) -> None:
        ip = self.get_client_ip(request)
        now = time.time()
        window_start = now - self.window_seconds

        # Clean timestamps older than the sliding window
        active_timestamps = [ts for ts in self.history.get(ip, []) if ts > window_start]

        if len(active_timestamps) >= self.max_requests:
            retry_after = max(1, int(self.window_seconds - (now - active_timestamps[0])) + 1)
            raise RateLimitExceeded(
                detail="Too many requests. Please try again later.",
                retry_after=retry_after,
            )

        active_timestamps.append(now)
        self.history[ip] = active_timestamps

    def reset(self) -> None:
        """Clear recorded request timestamps."""
        self.history.clear()


def create_rate_limiter(max_requests: int, window_seconds: int = 60) -> InMemoryRateLimiter:
    """Factory creating an InMemoryRateLimiter instance."""
    return InMemoryRateLimiter(max_requests=max_requests, window_seconds=window_seconds)


# Pre-configured rate limiters for core security endpoints
# Max 5 registrations per minute per IP for worker signup
worker_signup_limiter = create_rate_limiter(max_requests=5, window_seconds=60)

# Max 10 vouch submissions per minute per IP for witness vouches (shared site WiFi/NAT)
witness_vouch_limiter = create_rate_limiter(max_requests=10, window_seconds=60)
