"""Actra memory & persistent context layer."""

from .store import MemoryStore
from .api import (
    get_store,
    set_default_store,
    get_preference,
    set_preference,
    delete_preference,
    list_preferences,
    log_task_outcome,
    log_context_event,
    recent_context,
    get_task_history,
)

__all__ = [
    "MemoryStore",
    "get_store",
    "set_default_store",
    "get_preference",
    "set_preference",
    "delete_preference",
    "list_preferences",
    "log_task_outcome",
    "log_context_event",
    "recent_context",
    "get_task_history",
]
