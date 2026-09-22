"""Unit tests for Safari automation permissions gap detection and error handling."""

from unittest.mock import patch
import pytest

from actra.models import ToolResult
from actra.tools.browser import safari_read_page, safari_do_javascript
from actra.mac.permissions import check_safari_js_automation, SAFARI_JS_PERMISSION_INSTRUCTIONS


def test_safari_read_page_handles_permission_gap():
    """Verify safari_read_page returns clear actionable guidance on Apple Events privilege error."""
    with patch("actra.tools.browser.run_applescript", side_effect=RuntimeError("AppleScript error: Safari got an error: A privilege violation occurred. (-10004)")):
        res = safari_read_page()
        assert res.success is False
        assert res.error.code == "PERMISSION_DENIED"
        assert "Allow JavaScript from Apple Events" in res.error.message
        assert "Show features for web developers" in res.error.message


def test_safari_do_javascript_handles_permission_gap():
    """Verify safari_do_javascript returns actionable guidance when JS execution is not allowed."""
    with patch("actra.tools.browser.run_applescript", side_effect=RuntimeError("AppleScript error: Safari got an error: JavaScript execution is not allowed. (-2700)")):
        res = safari_do_javascript("document.title")
        assert res.success is False
        assert res.error.code == "PERMISSION_DENIED"
        assert "Settings" in res.error.message
        assert "Allow JavaScript from Apple Events" in res.error.message



def test_safari_read_page_success():
    """Verify safari_read_page returns page content when permitted."""
    with patch("actra.tools.browser.run_applescript", return_value="Welcome to Apple Developer"):
        res = safari_read_page()
        assert res.success is True
        assert res.data["content"] == "Welcome to Apple Developer"


def test_check_safari_js_automation_detection():
    """Verify check_safari_js_automation detects permission violation."""
    with patch("actra.mac.permissions.run_applescript", side_effect=RuntimeError("execution error: A privilege violation occurred. (-10004)")):
        assert check_safari_js_automation() is False

    with patch("actra.mac.permissions.run_applescript", return_value="2"):
        assert check_safari_js_automation() is True
