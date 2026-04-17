from collections import defaultdict, deque
from datetime import UTC, datetime
from typing import Callable

from fastapi import HTTPException, Request, status

from app.config.settings import settings


_REQUEST_LOGS: dict[str, deque[datetime]] = defaultdict(deque)


def rate_limit(
    max_requests: int = settings.API_RATE_LIMIT_MAX_REQUESTS,
    window_seconds: int = settings.API_RATE_LIMIT_WINDOW_SECONDS,
) -> Callable[[Request], None]:
    async def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{request.url.path}:{client_ip}"
        now = datetime.now(UTC)
        window = _REQUEST_LOGS[key]

        while window and (now - window[0]).total_seconds() > window_seconds:
            window.popleft()

        if len(window) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please retry in a minute.",
            )

        window.append(now)

    return dependency
