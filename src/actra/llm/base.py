from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Represents a tool call requested by the model."""
    id: str
    name: str
    arguments: dict[str, Any]


class Message(BaseModel):
    """Represents a message in the conversation history."""
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str = ""
    tool_call_id: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None
    raw: Any = None


class LLMResponse(BaseModel):
    """Represents the response from the LLM."""
    text: Optional[str] = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    raw: Any = None


class ToolSchema(BaseModel):
    """Represents a tool definition provided to the LLM."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema for the tool's parameters


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[ToolSchema]] = None
    ) -> LLMResponse:
        """Send messages to the model, optionally with tool definitions.

        Args:
            messages: A list of Message objects representing the conversation history.
            tools: An optional list of ToolSchema objects defining available tools.

        Returns:
            An LLMResponse containing the model's text response and/or tool calls.
        """
        pass
