import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    """In-memory, per-process request limiter for the paid AI endpoint.

    ponytail: state is per process, so it assumes one API instance (true on
    Render's free plan); use a shared store if the API is ever scaled out.
    """

    def __init__(self, window_seconds: float = 60.0) -> None:
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self._window:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True

    def clear(self) -> None:
        self._hits.clear()


chat_rate_limiter = SlidingWindowLimiter()
