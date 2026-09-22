"""Universal App Control Layer — Abstract AppAdapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from actra.models import SafetyLevel, ToolResult


class ActionType(str, Enum):
    """App-agnostic action classification for safety governance."""

    READ = "READ"               # Inspect, list, read, query state
    NAVIGATE = "NAVIGATE"       # Change view, open URL, switch tab
    INPUT = "INPUT"             # Type text, select item, fill form
    MUTATE = "MUTATE"           # Create, edit, move, delete content
    EXECUTE = "EXECUTE"         # Arbitrary code execution, JS eval, shell (NEVER auto-approved)
    SYSTEM = "SYSTEM"           # OS-level control, permissions, security changes (NEVER auto-approved)


# Actions in this set MUST NEVER be auto-approved, regardless of confirmation mode
NEVER_AUTO_APPROVED: frozenset[ActionType] = frozenset({
    ActionType.EXECUTE,
    ActionType.SYSTEM,
})


class AppAdapter(ABC):
    """Abstract base adapter for controlling macOS applications."""

    @property
    @abstractmethod
    def app_name(self) -> str:
        """Human-readable name of the application (e.g. 'Safari', 'Finder')."""
        pass

    @property
    @abstractmethod
    def bundle_id(self) -> str | None:
        """macOS CFBundleIdentifier (e.g. 'com.apple.Safari'), or None for system adapters."""
        pass

    @abstractmethod
    def discover(self) -> dict[str, Any]:
        """Discover the app's current runtime status, active windows, and capabilities."""
        pass

    @abstractmethod
    def inspect(self, target: str | None = None) -> dict[str, Any]:
        """Inspect a specific target element, document, or the active UI state."""
        pass

    @abstractmethod
    def act(self, action: str, action_type: ActionType, **kwargs: Any) -> ToolResult:
        """Dispatch a named action with the specified ActionType and parameters."""
        pass

    @abstractmethod
    def verify(self, action: str, expected: dict[str, Any]) -> bool:
        """Verify the outcome of an action against expected post-conditions."""
        pass

    def get_safety_level(self, action_type: ActionType) -> SafetyLevel:
        """Map an ActionType to a base SafetyLevel."""
        if action_type in NEVER_AUTO_APPROVED:
            return SafetyLevel.DANGEROUS
        if action_type == ActionType.MUTATE:
            return SafetyLevel.SENSITIVE
        return SafetyLevel.SAFE

    def is_never_auto_approved(self, action_type: ActionType) -> bool:
        """Return True if the action type cannot be bypassed by any confirmation policy."""
        return action_type in NEVER_AUTO_APPROVED
