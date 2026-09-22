from actra.models import ToolResult, SafetyLevel
from .registry import tool
from actra.mac import apple_events

@tool(
    name="open_application",
    description="Opens or activates a macOS app.",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        },
        "required": ["name"]
    },
    safety=SafetyLevel.SAFE
)
def open_application(name: str) -> ToolResult:
    try:
        apple_events.open_application(name)
        return ToolResult.ok("open_application", name=name)
    except Exception as e:
        return ToolResult.fail("open_application", "ERROR", str(e))

@tool(
    name="close_application",
    description="Quits a macOS app.",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        },
        "required": ["name"]
    },
    safety=SafetyLevel.SENSITIVE
)
def close_application(name: str) -> ToolResult:
    try:
        apple_events.close_application(name)
        return ToolResult.ok("close_application", name=name)
    except Exception as e:
        return ToolResult.fail("close_application", "ERROR", str(e))

@tool(
    name="activate_application",
    description="Brings an app to the front.",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        },
        "required": ["name"]
    },
    safety=SafetyLevel.SAFE
)
def activate_application(name: str) -> ToolResult:
    try:
        apple_events.activate_application(name)
        return ToolResult.ok("activate_application", name=name)
    except Exception as e:
        return ToolResult.fail("activate_application", "ERROR", str(e))

@tool(
    name="list_running_applications",
    description="Lists currently running applications.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    safety=SafetyLevel.SAFE
)
def list_running_applications() -> ToolResult:
    try:
        apps = apple_events.list_running_applications()
        return ToolResult.ok("list_running_applications", apps=apps)
    except Exception as e:
        return ToolResult.fail("list_running_applications", "ERROR", str(e))

@tool(
    name="get_active_application",
    description="Gets the name of the frontmost application.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    safety=SafetyLevel.SAFE
)
def get_active_application() -> ToolResult:
    try:
        app = apple_events.get_active_application()
        return ToolResult.ok("get_active_application", app=app)
    except Exception as e:
        return ToolResult.fail("get_active_application", "ERROR", str(e))
