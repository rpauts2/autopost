"""Helper functions."""

import asyncio
from typing import Any, Callable, Coroutine, Optional
from datetime import datetime, timezone


def get_timestamp() -> str:
    """Get current timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID."""
    timestamp = datetime.now(timezone.utc).timestamp()
    import random
    random_part = random.randint(1000, 9999)
    return f"{prefix}{int(timestamp * 1000)}{random_part}" if prefix else f"{int(timestamp * 1000)}{random_part}"


async def safe_async_call(
    coro: Coroutine,
    timeout: float = 30.0,
    default: Any = None,
    error_handler: Optional[Callable[[Exception], None]] = None
) -> Any:
    """Safely execute an async call with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        if error_handler:
            error_handler(asyncio.TimeoutError("Operation timed out"))
        return default
    except Exception as e:
        if error_handler:
            error_handler(e)
        return default


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely parse JSON."""
    import json
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default

