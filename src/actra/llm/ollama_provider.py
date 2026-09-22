from __future__ import annotations

import json
import re
import uuid
import logging
from typing import Any, Optional

import httpx

from .base import LLMProvider, LLMResponse, Message, ToolCall, ToolSchema

logger = logging.getLogger(__name__)


def _repair_json_arguments(raw_args: Any) -> dict[str, Any]:
    """Defensively parse or repair JSON arguments from tool calls."""
    if isinstance(raw_args, dict):
        return raw_args
    if not isinstance(raw_args, str):
        return {}

    raw_str = raw_args.strip()
    if not raw_str:
        return {}

    try:
        parsed = json.loads(raw_str)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    try:
        parsed = json.loads(raw_str, strict=False)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    cleaned = re.sub(r',\s*([\}\]])', r'\1', raw_str)
    try:
        parsed = json.loads(cleaned, strict=False)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    return {}


def _extract_text_tool_calls(text: str) -> list[ToolCall]:
    """Fallback parser if an open-weight model emits tool calls directly in text."""
    tool_calls: list[ToolCall] = []
    if not text:
        return tool_calls

    pattern = r'<tool_call\b[^>]*>(.*?)</tool_call>'
    matches = re.findall(pattern, text, re.DOTALL)

    for m in matches:
        try:
            data = json.loads(m.strip(), strict=False)
            if isinstance(data, dict) and 'name' in data:
                args = data.get('arguments', data.get('parameters', {}))
                tool_calls.append(
                    ToolCall(
                        id=f'call_{uuid.uuid4().hex[:8]}',
                        name=data['name'],
                        arguments=_repair_json_arguments(args)
                    )
                )
        except Exception:
            continue

    return tool_calls


class OllamaProvider(LLMProvider):
    """Local LLM Provider running Gemma 4 12B (MLX) via Ollama."""

    def __init__(
        self,
        model_name: str = 'gemma4:12b-mlx',
        host: str = 'http://localhost:11434',
        num_ctx: int = 8192,
        timeout: float = 120.0,
    ) -> None:
        self.model_name = model_name
        self.host = host.rstrip('/')
        self.num_ctx = num_ctx
        self.timeout = timeout
        self._chat_url = f'{self.host}/api/chat'

    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[ToolSchema]] = None
    ) -> LLMResponse:
        """Send chat messages and tool definitions to local Ollama instance."""
        payload_messages: list[dict[str, Any]] = []

        for msg in messages:
            item: dict[str, Any] = {'role': msg.role, 'content': msg.content or ''}
            if msg.tool_calls:
                item['tool_calls'] = [
                    {
                        'function': {
                            'name': tc.name,
                            'arguments': tc.arguments,
                        }
                    }
                    for tc in msg.tool_calls
                ]
            payload_messages.append(item)

        payload_tools: Optional[list[dict[str, Any]]] = None
        if tools:
            payload_tools = [
                {
                    'type': 'function',
                    'function': {
                        'name': tool_schema.name,
                        'description': tool_schema.description,
                        'parameters': tool_schema.parameters,
                    }
                }
                for tool_schema in tools
            ]

        request_body: dict[str, Any] = {
            'model': self.model_name,
            'messages': payload_messages,
            'stream': False,
            'options': {
                'num_ctx': self.num_ctx,
            }
        }

        if payload_tools:
            request_body['tools'] = payload_tools

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self._chat_url, json=request_body)
                response.raise_for_status()
                data = response.json()
        except httpx.ConnectError as e:
            raise RuntimeError(
                f'Could not connect to Ollama server at {self.host}. '
                f'Ensure Ollama is running ("ollama serve"). Error: {e}'
            ) from e
        except Exception as e:
            raise RuntimeError(f'Ollama API request failed: {e}') from e

        msg_data = data.get('message', {})
        raw_content = msg_data.get('content', '')
        raw_tool_calls = msg_data.get('tool_calls', [])

        extracted_calls: list[ToolCall] = []

        if raw_tool_calls:
            for tc in raw_tool_calls:
                func = tc.get('function', {})
                name = func.get('name', '')
                args = func.get('arguments', {})
                if name:
                    repaired_args = _repair_json_arguments(args)
                    extracted_calls.append(
                        ToolCall(
                            id=f'call_{uuid.uuid4().hex[:8]}',
                            name=name,
                            arguments=repaired_args
                        )
                    )
        elif raw_content and tools:
            extracted_calls = _extract_text_tool_calls(raw_content)

        return LLMResponse(
            text=raw_content if raw_content else None,
            tool_calls=extracted_calls,
            raw=data
        )
