"""A minimal cache abstraction so LocationService never depends on a
specific backend. `InMemoryLocationCache` is the default and requires no
infrastructure. A Redis-backed implementation could be added later behind
the same `LocationCache` interface without touching LocationService —
Redis is deliberately not required to run this app locally.
"""

import time
from threading import Lock
from typing import Any, Protocol


class LocationCache(Protocol):
    def get(self, key: str) -> Any | None: ...

    def set(self, key: str, value: Any, ttl_seconds: float) -> None: ...


class InMemoryLocationCache:
    """Process-local cache with per-entry TTL. Not shared across processes
    or restarts — fine for a single-instance prototype.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.monotonic() >= expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + ttl_seconds, value)


def make_cache_key(*parts: str | float) -> str:
    return ":".join(str(part) for part in parts)
