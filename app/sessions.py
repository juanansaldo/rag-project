import time
from threading import Lock

from app.config import SESSION_TTL_SECONDS, SESSION_CLEANUP_INTERVAL_SECONDS

_last_seen: dict[str, float] = {}
_lock = Lock()
_last_cleanup_ts = 0.0


def touch_session(session_id: str) -> None:
    with _lock:
        _last_seen[session_id] = time.time()


def remove_session_tracking(session_id: str) -> None:
    with _lock:
        _last_seen.pop(session_id, None)


def maybe_get_expired_sessions() -> list[str]:
    """
    Return expired session IDs on cleanup cadence.
    Cleanup runs at most every SESSION_CLEANUP_INTERVAL_SECONDS.
    """
    global _last_cleanup_ts
    now = time.time()

    with _lock:
        if now - _last_cleanup_ts < SESSION_CLEANUP_INTERVAL_SECONDS:
            return []
        
        expired = [sid for sid, ts in _last_seen.items() if now - ts > SESSION_TTL_SECONDS]
        for sid in expired:
            _last_seen.pop(sid, None)
        
        _last_cleanup_ts = now
        return expired