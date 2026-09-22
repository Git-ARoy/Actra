"""Safety gate — tiered approval policies, sensitive path protection, and granular confirmation."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Callable, Union

from actra.models import SafetyLevel


# Regex / substring patterns for sensitive file paths and secret stores
SENSITIVE_PATH_PATTERNS = [
    r"(^|/)\.ssh(/|$)",
    r"(^|/)\.aws(/|$)",
    r"(^|/)\.azure(/|$)",
    r"(^|/)\.gnupg(/|$)",
    r"(^|/)\.config/gcloud(/|$)",
    r"Library/Keychains(/|$)",
    r"Library/Safari(/|$)",
    r"Library/Application Support/Google/Chrome(/|$)",
    r"Library/Application Support/BraveSoftware(/|$)",
    r"Cookies\.binarycookies",
    r"Login Data",
    r"(^|/)\.env(\.[a-zA-Z0-9_-]+)?$",
    r"(^|/)\.(bash|zsh)_history$",
    r"(^|/)\.(bash_profile|zprofile|bashrc|zshrc)$",
    r"id_rsa",
    r"id_ed25519",
    r"\.pem$",
    r"\.key$",
]

_COMPILED_SENSITIVE_PATTERNS = [re.compile(pat, re.IGNORECASE) for pat in SENSITIVE_PATH_PATTERNS]


def is_sensitive_path(path: str | Path | None) -> bool:
    """Check whether a path points to sensitive credentials, keys, dotfiles, or profile data."""
    if not path:
        return False
    path_str = str(path).strip()
    expanded = str(Path(path_str).expanduser())

    for pattern in _COMPILED_SENSITIVE_PATTERNS:
        if pattern.search(path_str) or pattern.search(expanded):
            return True
    return False


class SafetyGate:
    """Evaluates tool execution requests against safety tiers and confirmation policies."""

    def __init__(
        self,
        confirmation_mode: Union[str, bool] = "none",
        prompt_delegate: Callable[[str, dict[str, Any], SafetyLevel], bool] | None = None,
    ):
        """Initialize SafetyGate.

        confirmation_mode can be:
        - "none" / False: interactive confirmation required for SENSITIVE and DANGEROUS tiers (default)
        - "sensitive" / True: bypass SENSITIVE confirmation, still require confirmation for DANGEROUS
        - "all": bypass confirmation for standard tiers (scripted/unattended mode)
        NOTE: Tools/actions in NEVER_AUTO_APPROVED (e.g. EXECUTE, SYSTEM) can NEVER be bypassed even with "all".
        """
        if isinstance(confirmation_mode, bool):
            self._confirmation_mode = "none" if confirmation_mode else "all"
        else:
            mode_lower = str(confirmation_mode).lower().strip()
            if mode_lower in ("all", "sensitive", "none"):
                self._confirmation_mode = mode_lower
            else:
                self._confirmation_mode = "none"

        self._prompt_delegate = prompt_delegate

    def set_prompt_delegate(
        self, delegate: Callable[[str, dict[str, Any], SafetyLevel], bool] | None
    ) -> None:
        """Set or update the confirmation prompt delegate (e.g. HUD)."""
        self._prompt_delegate = delegate

    @property
    def confirmation_mode(self) -> str:
        return self._confirmation_mode

    def is_never_auto_approved(
        self, tool_name: str, action_type: Any | None = None
    ) -> bool:
        """Check if an action is strictly non-bypassable regardless of confirmation mode."""
        if action_type is not None:
            # Check ActionType enum value
            val = getattr(action_type, "value", str(action_type))
            if val in ("EXECUTE", "SYSTEM"):
                return True
        # Specific tools that execute arbitrary script / system changes
        if tool_name in ("safari_do_javascript", "execute_command", "terminal_run", "run_script"):
            return True
        return False

    def get_effective_safety_level(
        self, tool_name: str, base_safety: SafetyLevel, arguments: dict[str, Any]
    ) -> SafetyLevel:
        """Determine effective safety level by inspecting tool type, arguments, and target paths."""
        # 1. Inherently dangerous or executable tools remain DANGEROUS
        if base_safety == SafetyLevel.DANGEROUS or self.is_never_auto_approved(tool_name):
            return SafetyLevel.DANGEROUS

        # 2. Check for sensitive paths in filesystem/app arguments
        target_paths = []
        for key in ("path", "source", "destination", "directory"):
            val = arguments.get(key)
            if isinstance(val, str):
                target_paths.append(val)

        for p in target_paths:
            if is_sensitive_path(p):
                # Destructive/modifying ops on sensitive paths are DANGEROUS
                if tool_name in ("write_file", "create_file", "delete_file", "move_file"):
                    return SafetyLevel.DANGEROUS
                # Read/list ops on sensitive paths are elevated to SENSITIVE
                return SafetyLevel.SENSITIVE

        # 3. Check for file overwrite conditions in copy_file / move_file
        if tool_name in ("copy_file", "move_file") and arguments.get("overwrite") is True:
            dst = arguments.get("destination")
            if dst and Path(dst).expanduser().exists():
                return SafetyLevel.SENSITIVE

        return base_safety

    def check(
        self,
        tool_name: str,
        safety: SafetyLevel,
        arguments: dict[str, Any],
        action_type: Any | None = None,
    ) -> bool:
        """Check if a tool call should proceed based on effective safety level and confirmation mode.

        Returns True if approved, False if denied.
        """
        # Hard Rule: NEVER_AUTO_APPROVED actions (EXECUTE, SYSTEM) always require confirmation
        if self.is_never_auto_approved(tool_name, action_type):
            return self._prompt_user(tool_name, arguments, SafetyLevel.DANGEROUS)

        effective_level = self.get_effective_safety_level(tool_name, safety, arguments)

        # SAFE: always proceeds
        if effective_level == SafetyLevel.SAFE:
            return True

        # SENSITIVE: check confirmation mode
        if effective_level == SafetyLevel.SENSITIVE:
            if self._confirmation_mode in ("sensitive", "all"):
                return True
            return self._prompt_user(tool_name, arguments, effective_level)

        # DANGEROUS: only bypassed if confirmation_mode == "all"
        if effective_level == SafetyLevel.DANGEROUS:
            if self._confirmation_mode == "all":
                return True
            return self._prompt_user(tool_name, arguments, effective_level)

        return True

    def _prompt_user(
        self, tool_name: str, arguments: dict[str, Any], level: SafetyLevel
    ) -> bool:
        """Confirmation prompt (delegates to HUD if available, else CLI)."""
        if self._prompt_delegate is not None:
            try:
                hud_result = self._prompt_delegate(tool_name, arguments, level)
                if hud_result is not None:
                    return hud_result
            except Exception:
                pass

        print(f"\n[SAFETY CHECK: {level.name}]")
        print(f"Tool: {tool_name}")
        print(f"Arguments: {arguments}")
        try:
            response = input("Proceed? [y/N]: ").strip().lower()
            return response in ["y", "yes"]
        except (EOFError, KeyboardInterrupt):
            return False
