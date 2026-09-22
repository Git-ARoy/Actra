"""No-Op Example Adapter for testing routing without side effects."""

from __future__ import annotations

from typing import Any

from actra.mac.app_adapter import ActionType, AppAdapter
from actra.models import ToolResult


class NoOpAdapter(AppAdapter):
    """Example stub adapter proving registration and routing without OS side-effects."""

    @property
    def app_name(self) -> str:
        return "NoOp"

    @property
    def bundle_id(self) -> str:
        return "com.actra.noop"

    def discover(self) -> dict[str, Any]:
        return {
            "app_name": self.app_name,
            "bundle_id": self.bundle_id,
            "status": "ready",
            "simulated": True,
            "capabilities": ["ping", "echo", "test_action"],
        }

    def inspect(self, target: str | None = None) -> dict[str, Any]:
        return {
            "target": target,
            "inspected": True,
            "simulated": True,
        }

    def act(self, action: str, action_type: ActionType, **kwargs: Any) -> ToolResult:
        return ToolResult.ok(
            "noop",
            action=action,
            action_type=action_type.value,
            params=kwargs,
            message="NoOp action simulated successfully."
        )

    def verify(self, action: str, expected: dict[str, Any]) -> bool:
        # No-op always satisfies expectations for simulated tests
        return True
