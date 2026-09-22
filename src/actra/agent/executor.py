"""Executor — validates, safety-checks, and dispatches tool calls."""

from __future__ import annotations

from typing import Any

from actra.logging import ExecutionLogger
from actra.models import ToolResult
from actra.tools.registry import ToolRegistry
from actra.tools.safety import SafetyGate


class Executor:
    """Invokes tools with safety checks, logging, and error handling."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        safety_gate: SafetyGate,
        logger: ExecutionLogger,
    ) -> None:
        self._registry = tool_registry
        self._safety = safety_gate
        self._logger = logger

    def execute(
        self,
        task_id: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        """Execute a tool call with full safety + logging pipeline.

        1. Check the tool exists.
        2. Check safety level and prompt for confirmation if needed.
        3. Log the call.
        4. Execute.
        5. Log the result.
        6. Return the result.
        """
        # 1. Tool existence
        tool_def = self._registry.get(tool_name)
        if tool_def is None:
            result = ToolResult.fail(
                tool_name, "TOOL_NOT_FOUND", f"No tool named '{tool_name}' is registered."
            )
            self._logger.tool_result(task_id, tool_name, result.model_dump())
            return result

        # 2. Safety gate
        approved = self._safety.check(tool_name, tool_def.safety, arguments)
        if not approved:
            result = ToolResult.fail(
                tool_name, "USER_DENIED", "User denied the action."
            )
            self._logger.tool_result(task_id, tool_name, result.model_dump())
            return result

        # 3. Log the call
        self._logger.tool_call(task_id, tool_name, arguments)

        # 4. Execute
        try:
            result = self._registry.execute(tool_name, arguments)
        except Exception as e:
            result = ToolResult.fail(tool_name, "EXECUTION_EXCEPTION", str(e))

        # 5. Log the result
        self._logger.tool_result(task_id, tool_name, result.model_dump())

        return result
