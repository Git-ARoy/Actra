"""Safari Application Adapter."""

from __future__ import annotations

from typing import Any

from actra.mac import apple_events
from actra.mac.app_adapter import ActionType, AppAdapter
from actra.models import ToolResult
from actra.tools import browser


class SafariAdapter(AppAdapter):
    """Adapter for controlling the Apple Safari web browser."""

    @property
    def app_name(self) -> str:
        return "Safari"

    @property
    def bundle_id(self) -> str:
        return "com.apple.Safari"

    def discover(self) -> dict[str, Any]:
        running_apps = apple_events.list_running_apps()
        is_running = "Safari" in running_apps
        result: dict[str, Any] = {
            "app_name": self.app_name,
            "bundle_id": self.bundle_id,
            "is_running": is_running,
            "capabilities": ["navigate", "search", "read_page", "get_url", "get_title", "do_javascript"],
        }
        if is_running:
            try:
                url = apple_events.run_applescript('tell application "Safari" to get URL of current tab of front window').strip()
                title = apple_events.run_applescript('tell application "Safari" to get name of front window').strip()
                result["active_url"] = url
                result["active_title"] = title
            except Exception:
                pass
        return result

    def inspect(self, target: str | None = None) -> dict[str, Any]:
        target_lower = (target or "").lower().strip()
        if target_lower in ("url", "current_url"):
            res = browser.safari_get_url()
            return res.model_dump()
        elif target_lower in ("title", "window_title"):
            res = browser.safari_get_title()
            return res.model_dump()
        elif target_lower in ("page", "content", "text"):
            res = browser.safari_read_page()
            return res.model_dump()
        else:
            return self.discover()

    def act(self, action: str, action_type: ActionType, **kwargs: Any) -> ToolResult:
        action_clean = action.lower().strip()
        if action_clean in ("open", "launch", "activate"):
            return browser.safari_open()
        elif action_clean in ("navigate", "open_url"):
            return browser.safari_navigate(url=kwargs.get("url", ""))
        elif action_clean == "search":
            return browser.safari_search(query=kwargs.get("query", ""))
        elif action_clean in ("get_url", "current_url"):
            return browser.safari_get_url()
        elif action_clean in ("get_title", "title"):
            return browser.safari_get_title()
        elif action_clean in ("read_page", "extract_text"):
            return browser.safari_read_page(max_chars=kwargs.get("max_chars", 10000))
        elif action_clean in ("do_javascript", "execute_js", "eval"):
            return browser.safari_do_javascript(javascript=kwargs.get("javascript", ""))
        else:
            return ToolResult.fail("safari_adapter", "UNKNOWN_ACTION", f"Unknown action '{action}' for Safari")

    def verify(self, action: str, expected: dict[str, Any]) -> bool:
        if "url_contains" in expected:
            res = browser.safari_get_url()
            if not res.success or not res.data or expected["url_contains"] not in res.data.get("url", ""):
                return False
        if "title_contains" in expected:
            res = browser.safari_get_title()
            if not res.success or not res.data or expected["title_contains"] not in res.data.get("title", ""):
                return False
        if "is_running" in expected:
            running = "Safari" in apple_events.list_running_apps()
            if running != expected["is_running"]:
                return False
        return True
