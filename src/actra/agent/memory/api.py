"""Public API for Actra memory and context layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from actra.models import Task
from .store import MemoryStore

_default_store: MemoryStore | None = None


def get_store(db_path: Path | str | None = None) -> MemoryStore:
    """Get or initialize the global memory store."""
    global _default_store
    if _default_store is None or db_path is not None:
        if db_path is not None:
            return MemoryStore(db_path)
        _default_store = MemoryStore()
    return _default_store


def set_default_store(store: MemoryStore) -> None:
    """Override the global default memory store (useful for tests)."""
    global _default_store
    _default_store = store


def get_preference(key: str, default: str | None = None) -> str | None:
    """Retrieve a preference value by key."""
    return get_store().get_preference(key, default)


def set_preference(key: str, value: str) -> None:
    """Set a preference value by key."""
    get_store().set_preference(key, value)


def delete_preference(key: str) -> bool:
    """Delete a preference by key."""
    return get_store().delete_preference(key)


def list_preferences() -> dict[str, str]:
    """Return all stored preferences."""
    return get_store().list_preferences()


def log_task_outcome(task: Task) -> None:
    """Record a completed or failed task outcome in memory."""
    get_store().log_task_outcome(task)


def log_context_event(task_id: str | None, event_type: str, content: str) -> None:
    """Record an event in the context log."""
    get_store().log_context_event(task_id, event_type, content)


def recent_context(limit: int = 10) -> list[dict[str, Any]]:
    """Retrieve recent context entries across tasks and system events."""
    return get_store().recent_context(limit)


def get_task_history(limit: int = 20) -> list[dict[str, Any]]:
    """Retrieve recent task execution records."""
    return get_store().get_task_history(limit)
