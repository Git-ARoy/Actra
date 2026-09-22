"""Structured execution logger with secret redaction."""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Patterns to redact from logs
_SECRET_PATTERNS = [
    re.compile(r"(api[_-]?key|token|secret|password|credential)[\"']?\s*[:=]\s*[\"']?[\w.+/=-]{8,}", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),  # Google API key pattern
    re.compile(r"sk-[A-Za-z0-9]{20,}"),  # OpenAI key pattern
]

_REDACTED = "[REDACTED]"


def _redact(text: str) -> str:
    """Redact secrets from a string."""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(_REDACTED, text)
    return text


def _redact_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Deep-redact secrets from a dictionary."""
    result: dict[str, Any] = {}
    sensitive_keys = {"api_key", "token", "secret", "password", "credential", "key"}
    for k, v in d.items():
        if any(s in k.lower() for s in sensitive_keys):
            result[k] = _REDACTED
        elif isinstance(v, dict):
            result[k] = _redact_dict(v)
        elif isinstance(v, str):
            result[k] = _redact(v)
        elif isinstance(v, list):
            result[k] = [
                _redact_dict(item) if isinstance(item, dict)
                else _redact(item) if isinstance(item, str)
                else item
                for item in v
            ]
        else:
            result[k] = v
    return result


class ExecutionLogger:
    """Writes structured JSON execution traces and human-readable console output."""

    def __init__(self, log_dir: Path, level: str = "INFO") -> None:
        self._log_dir = log_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # JSON trace file
        self._trace_path = self._log_dir / f"trace_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl"

        # Python logger for console output
        self._logger = logging.getLogger("actra")
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
            )
            self._logger.addHandler(handler)

    # ------------------------------------------------------------------
    # Structured trace
    # ------------------------------------------------------------------

    def trace(
        self,
        *,
        task_id: str,
        event: str,
        tool: str | None = None,
        arguments: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        verification: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Append a structured event to the trace file."""
        record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "event": event,
        }
        if tool:
            record["tool"] = tool
        if arguments:
            record["arguments"] = _redact_dict(arguments)
        if result:
            record["result"] = _redact_dict(result)
        if error:
            record["error"] = _redact(error)
        if verification:
            record["verification"] = verification
        if extra:
            record["extra"] = _redact_dict(extra)

        with open(self._trace_path, "a") as f:
            f.write(json.dumps(record) + "\n")

    # ------------------------------------------------------------------
    # Console helpers (delegate to Python logging)
    # ------------------------------------------------------------------

    def info(self, msg: str, *args: Any) -> None:
        self._logger.info(msg, *args)

    def warning(self, msg: str, *args: Any) -> None:
        self._logger.warning(msg, *args)

    def error(self, msg: str, *args: Any) -> None:
        self._logger.error(msg, *args)

    def debug(self, msg: str, *args: Any) -> None:
        self._logger.debug(msg, *args)

    def step(self, task_id: str, msg: str) -> None:
        """Log a high-visibility agent step."""
        self._logger.info("🔹 [%s] %s", task_id[:8], msg)
        self.trace(task_id=task_id, event="step", extra={"message": msg})

    def tool_call(self, task_id: str, tool: str, arguments: dict[str, Any]) -> None:
        """Log a tool invocation."""
        self._logger.info("🔧 [%s] %s(%s)", task_id[:8], tool, ", ".join(f"{k}={v!r}" for k, v in _redact_dict(arguments).items()))
        self.trace(task_id=task_id, event="tool_started", tool=tool, arguments=arguments)

    def tool_result(self, task_id: str, tool: str, result: dict[str, Any]) -> None:
        """Log a tool result."""
        success = result.get("success", False)
        icon = "✅" if success else "❌"
        self._logger.info("%s [%s] %s → %s", icon, task_id[:8], tool, "success" if success else result.get("error", "failed"))
        self.trace(task_id=task_id, event="tool_completed", tool=tool, result=result)
