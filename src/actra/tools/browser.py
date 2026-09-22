from actra.models import ToolResult, SafetyLevel
from .registry import tool
from actra.mac.apple_events import run_applescript
from actra.mac.permissions import SAFARI_JS_PERMISSION_INSTRUCTIONS
import urllib.parse


def _handle_safari_js_error(e: Exception, tool_name: str) -> ToolResult:
    """Format AppleScript JavaScript permission errors into actionable instructions."""
    err_str = str(e)
    err_lower = err_str.lower()
    if (
        "privilege violation" in err_lower
        or "not allowed" in err_lower
        or "-10004" in err_lower
        or "-1728" in err_lower
        or "-2700" in err_lower
        or "do javascript" in err_lower
    ):
        return ToolResult.fail(
            tool_name,
            "PERMISSION_DENIED",
            f"Safari JavaScript automation is disabled in macOS.\n\n{SAFARI_JS_PERMISSION_INSTRUCTIONS}"
        )
    return ToolResult.fail(tool_name, "ERROR", err_str)


@tool(
    name="safari_open",
    description="Opens the Safari browser.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    safety=SafetyLevel.SAFE
)
def safari_open() -> ToolResult:
    script = 'tell application "Safari" to activate'
    try:
        run_applescript(script)
        return ToolResult.ok("safari_open")
    except Exception as e:
        return ToolResult.fail("safari_open", "ERROR", str(e))


@tool(
    name="safari_navigate",
    description="Navigates Safari to a specified URL.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string"}
        },
        "required": ["url"]
    },
    safety=SafetyLevel.SAFE
)
def safari_navigate(url: str) -> ToolResult:
    script = f'''
    tell application "Safari"
        activate
        open location "{url}"
    end tell
    '''
    try:
        run_applescript(script)
        return ToolResult.ok("safari_navigate", url=url)
    except Exception as e:
        return ToolResult.fail("safari_navigate", "ERROR", str(e))


@tool(
    name="safari_search",
    description="Searches Google via Safari.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    },
    safety=SafetyLevel.SAFE
)
def safari_search(query: str) -> ToolResult:
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    script = f'''
    tell application "Safari"
        activate
        open location "{url}"
    end tell
    '''
    try:
        run_applescript(script)
        return ToolResult.ok("safari_search", query=query, url=url)
    except Exception as e:
        return ToolResult.fail("safari_search", "ERROR", str(e))


@tool(
    name="safari_get_url",
    description="Gets the URL of the current tab in Safari.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    safety=SafetyLevel.SAFE
)
def safari_get_url() -> ToolResult:
    script = 'tell application "Safari" to get URL of current tab of front window'
    try:
        url = run_applescript(script).strip()
        return ToolResult.ok("safari_get_url", url=url)
    except Exception as e:
        return ToolResult.fail("safari_get_url", "ERROR", str(e))


@tool(
    name="safari_get_title",
    description="Gets the title of the front window in Safari.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    safety=SafetyLevel.SAFE
)
def safari_get_title() -> ToolResult:
    script = 'tell application "Safari" to get name of front window'
    try:
        title = run_applescript(script).strip()
        return ToolResult.ok("safari_get_title", title=title)
    except Exception as e:
        return ToolResult.fail("safari_get_title", "ERROR", str(e))


@tool(
    name="safari_read_page",
    description="Extracts the text content of the active webpage in Safari.",
    parameters={
        "type": "object",
        "properties": {
            "max_chars": {
                "type": "integer",
                "description": "Maximum characters to return (default 10000)"
            }
        },
        "required": []
    },
    safety=SafetyLevel.SAFE
)
def safari_read_page(max_chars: int = 10000) -> ToolResult:
    """Read readable inner text from active Safari tab."""
    script = '''
    tell application "Safari"
        if (count of windows) = 0 then
            error "No Safari windows are currently open."
        end if
        do JavaScript "document.body ? document.body.innerText : ''" in current tab of front window
    end tell
    '''
    try:
        raw_text = run_applescript(script)
        if len(raw_text) > max_chars:
            raw_text = raw_text[:max_chars] + f"\n... [truncated to {max_chars} characters]"
        return ToolResult.ok("safari_read_page", content=raw_text, length=len(raw_text))
    except Exception as e:
        return _handle_safari_js_error(e, "safari_read_page")


@tool(
    name="safari_do_javascript",
    description="Executes arbitrary JavaScript in the current Safari tab and returns the result.",
    parameters={
        "type": "object",
        "properties": {
            "javascript": {
                "type": "string",
                "description": "JavaScript code string to evaluate in the active tab"
            }
        },
        "required": ["javascript"]
    },
    safety=SafetyLevel.SENSITIVE
)
def safari_do_javascript(javascript: str) -> ToolResult:
    """Execute JavaScript in active Safari tab."""
    escaped_js = javascript.replace('\\', '\\\\').replace('"', '\\"')
    script = f'''
    tell application "Safari"
        if (count of windows) = 0 then
            error "No Safari windows are currently open."
        end if
        do JavaScript "{escaped_js}" in current tab of front window
    end tell
    '''
    try:
        res = run_applescript(script)
        return ToolResult.ok("safari_do_javascript", result=res)
    except Exception as e:
        return _handle_safari_js_error(e, "safari_do_javascript")
