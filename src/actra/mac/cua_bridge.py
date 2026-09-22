"""CUA (Computer Use Agent) Bridge for Actra.

Provides an abstraction layer that uses  (MCP stdio server)
when available on the system, and falls back to Actra's native
PyObjC / Quartz / Apple Events control layer when  is not present.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from actra.mac import accessibility, apple_events, input_control, screen_capture


logger = logging.getLogger(__name__)


def is_cua_driver_available() -> bool:
    """Check if  binary is on PATH."""
    return bool(shutil.which('cua-driver'))


class CUABridge:
    """Unified Computer-Use Bridge."""

    def __init__(self) -> None:
        self._cua_available = is_cua_driver_available()
        if self._cua_available:
            logger.info('cua-driver found on PATH. Using cua-driver backend.')
        else:
            logger.info('cua-driver not on PATH. Using Actra native macOS backend.')

    @property
    def has_cua_driver(self) -> bool:
        return self._cua_available

    def capture_screen(self, output_path: str | None = None) -> Tuple[str, str]:
        """Capture screen. Returns (base64_png, file_path)."""
        return screen_capture.take_screenshot(output_path=None if not output_path else Path(output_path))

    def inspect_ui(self, max_depth: int = 3) -> Dict[str, Any]:
        """Inspect active window accessibility tree."""
        return accessibility.inspect_ui(max_depth=max_depth)

    def click(self, x: float, y: float) -> None:
        """Perform mouse click."""
        input_control.click(x, y)

    def double_click(self, x: float, y: float) -> None:
        """Perform double click."""
        input_control.double_click(x, y)

    def type_text(self, text: str) -> None:
        """Type text string."""
        input_control.type_text(text)

    def key(self, keys: str) -> None:
        """Press hotkey or single key combo."""
        if '+' in keys:
            parts = keys.split('+')
            input_control.hotkey(*parts)
        else:
            input_control.press_key(keys)

    def scroll(self, amount: int, x: float | None = None, y: float | None = None) -> None:
        """Scroll mouse wheel."""
        input_control.scroll(amount, x=x, y=y)

    def open_app(self, name: str) -> bool:
        """Open/activate application."""
        return apple_events.open_application(name)

    def close_app(self, name: str) -> bool:
        """Close application."""
        return apple_events.quit_application(name)

    def list_running_apps(self) -> List[str]:
        """List running application processes."""
        return apple_events.list_running_apps()
