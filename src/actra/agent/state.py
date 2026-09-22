"""Task lifecycle state machine."""

from __future__ import annotations

from actra.models import Task, TaskStatus

# Valid state transitions
_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.RECEIVED: {TaskStatus.AUTHENTICATING, TaskStatus.PLANNING, TaskStatus.SYSTEM_ALERT, TaskStatus.BLOCKED, TaskStatus.CANCELLED, TaskStatus.FAILED},
    TaskStatus.AUTHENTICATING: {TaskStatus.PLANNING, TaskStatus.BLOCKED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.PLANNING: {TaskStatus.EXECUTING, TaskStatus.VERIFYING, TaskStatus.COMPLETED, TaskStatus.WAITING_FOR_CONFIRMATION, TaskStatus.SYSTEM_ALERT, TaskStatus.BLOCKED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.EXECUTING: {TaskStatus.OBSERVING, TaskStatus.VERIFYING, TaskStatus.BLOCKED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.WAITING_FOR_CONFIRMATION},
    TaskStatus.OBSERVING: {TaskStatus.VERIFYING, TaskStatus.EXECUTING, TaskStatus.PLANNING, TaskStatus.BLOCKED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.VERIFYING: {TaskStatus.COMPLETED, TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.BLOCKED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.WAITING_FOR_CONFIRMATION: {TaskStatus.EXECUTING, TaskStatus.PLANNING, TaskStatus.BLOCKED, TaskStatus.CANCELLED, TaskStatus.FAILED},
    TaskStatus.SYSTEM_ALERT: {TaskStatus.PLANNING, TaskStatus.BLOCKED, TaskStatus.CANCELLED, TaskStatus.FAILED},
    TaskStatus.BLOCKED: {TaskStatus.AUTHENTICATING, TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.CANCELLED, TaskStatus.FAILED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: set(),
    TaskStatus.CANCELLED: set(),
}



class StateError(Exception):
    """Raised when an invalid state transition is attempted."""


def transition(task: Task, new_status: TaskStatus) -> None:
    """Transition a task to a new status, validating the transition.

    Raises:
        StateError: If the transition is not allowed.
    """
    allowed = _TRANSITIONS.get(task.status, set())
    if new_status not in allowed:
        raise StateError(
            f"Cannot transition from {task.status.value} to {new_status.value}. "
            f"Allowed: {', '.join(s.value for s in allowed) if allowed else 'none (terminal state)'}"
        )
    task.mark(new_status)


def is_terminal(status: TaskStatus) -> bool:
    """Check if a status is terminal (no further transitions)."""
    return status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}
