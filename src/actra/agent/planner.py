"""Planner — sends goals + context + tool schemas to the LLM and gets back tool calls."""

from __future__ import annotations

from typing import Any

from actra.llm.base import LLMProvider, LLMResponse, ToolSchema, ToolCall
from actra.agent.context import ContextManager
from actra.tools.registry import ToolRegistry


class Planner:
    """Coordinates with the LLM to determine the next action.

    The planner sends the current conversation context and available tool
    schemas to the LLM and receives either a tool call or a text response.
    """

    def __init__(
        self,
        llm: LLMProvider,
        tool_registry: ToolRegistry,
    ) -> None:
        self._llm = llm
        self._registry = tool_registry

    def next_action(self, context: ContextManager) -> LLMResponse:
        """Ask the LLM for the next action given current context.

        Returns:
            LLMResponse with either tool_calls (actions to take) or text
            (completion message / clarification request).
        """
        # Build tool schemas for the LLM
        raw_schemas = self._registry.list_schemas()
        tool_schemas = [
            ToolSchema(
                name=s["name"],
                description=s["description"],
                parameters=s["parameters"],
            )
            for s in raw_schemas
        ]

        # Call the LLM
        response = self._llm.chat(
            messages=context.messages,
            tools=tool_schemas if tool_schemas else None,
        )

        return response
