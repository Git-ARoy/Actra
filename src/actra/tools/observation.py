from actra.models import ToolResult, SafetyLevel
from .registry import tool
from actra.mac import screen_capture, accessibility

@tool(
    name="take_screenshot",
    description="Captures the screen and returns base64 data and file path.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    safety=SafetyLevel.SAFE
)
def take_screenshot() -> ToolResult:
    try:
        b64, file_path = screen_capture.take_screenshot()
        return ToolResult.ok("take_screenshot", base64=b64, file_path=file_path)
    except Exception as e:
        return ToolResult.fail("take_screenshot", "ERROR", str(e))

@tool(
    name="get_window_info",
    description="Gets information about the frontmost window.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    safety=SafetyLevel.SAFE
)
def get_window_info() -> ToolResult:
    try:
        info = screen_capture.get_window_info()
        return ToolResult.ok("get_window_info", info=info)
    except Exception as e:
        return ToolResult.fail("get_window_info", "ERROR", str(e))

@tool(
    name="inspect_ui",
    description="Gets the structured accessibility tree of the frontmost application with element IDs (@e1, @e2, etc.) for semantic clicking and typing. Pruned to actionable elements by default.",
    parameters={
        "type": "object",
        "properties": {
            "max_depth": {
                "type": "integer",
                "description": "Maximum tree depth to inspect (default 4)"
            },
            "full_tree": {
                "type": "boolean",
                "description": "Whether to return the complete unpruned accessibility tree including layout containers (default false)"
            }
        },
        "required": []
    },
    safety=SafetyLevel.SAFE
)
def inspect_ui(max_depth: int = 4, full_tree: bool = False) -> ToolResult:
    try:
        ui_tree = accessibility.inspect_ui(max_depth=max_depth, full_tree=full_tree)
        return ToolResult.ok("inspect_ui", tree=ui_tree)
    except Exception as e:
        return ToolResult.fail("inspect_ui", "ERROR", str(e))

