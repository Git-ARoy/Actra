from actra.models import ToolResult, SafetyLevel
from .registry import tool
from actra.mac import input_control, accessibility

@tool(
    name="click_element",
    description="Clicks a UI element semantically by element ID (e.g. '@e3') or role/title (e.g. 'button:Save') found in inspect_ui. Preferred over coordinate clicking.",
    parameters={
        "type": "object",
        "properties": {
            "element_ref": {
                "type": "string",
                "description": "Element reference ID (e.g. '@e1', '@e5') or descriptor ('button:Submit', 'Search') from inspect_ui"
            },
            "action": {
                "type": "string",
                "description": "Accessibility action to perform (default 'AXPress')"
            }
        },
        "required": ["element_ref"]
    },
    safety=SafetyLevel.SENSITIVE
)
def click_element(element_ref: str, action: str = "AXPress") -> ToolResult:
    try:
        success = accessibility.click_element(element_ref=element_ref, action=action)
        if success:
            return ToolResult.ok("click_element", element_ref=element_ref, action=action)
        return ToolResult.fail("click_element", "ELEMENT_NOT_FOUND", f"Could not resolve or click element: {element_ref}")
    except Exception as e:
        return ToolResult.fail("click_element", "ERROR", str(e))

@tool(
    name="type_into_element",
    description="Types text directly into a UI element (text field, search bar, etc.) semantically by element ID (e.g. '@e2') or role/title. Preferred over blind typing.",
    parameters={
        "type": "object",
        "properties": {
            "element_ref": {
                "type": "string",
                "description": "Element reference ID (e.g. '@e2') or descriptor ('field:Search') from inspect_ui"
            },
            "text": {
                "type": "string",
                "description": "Text content to type or set into the element"
            },
            "clear_first": {
                "type": "boolean",
                "description": "Whether to select all and clear existing content before typing (default false)"
            }
        },
        "required": ["element_ref", "text"]
    },
    safety=SafetyLevel.SENSITIVE
)
def type_into_element(element_ref: str, text: str, clear_first: bool = False) -> ToolResult:
    try:
        success = accessibility.type_into_element(element_ref=element_ref, text=text, clear_first=clear_first)
        if success:
            return ToolResult.ok("type_into_element", element_ref=element_ref, text=text)
        return ToolResult.fail("type_into_element", "ELEMENT_NOT_FOUND", f"Could not resolve or type into element: {element_ref}")
    except Exception as e:
        return ToolResult.fail("type_into_element", "ERROR", str(e))

@tool(
    name="click",
    description="Clicks at raw screen coordinates (x, y). Fallback only when semantic element cannot be found with inspect_ui.",
    parameters={
        "type": "object",
        "properties": {
            "x": {"type": "number"},
            "y": {"type": "number"}
        },
        "required": ["x", "y"]
    },
    safety=SafetyLevel.SENSITIVE
)
def click(x: float, y: float) -> ToolResult:
    try:
        input_control.click(x, y)
        return ToolResult.ok("click", x=x, y=y)
    except Exception as e:
        return ToolResult.fail("click", "ERROR", str(e))

@tool(
    name="double_click",
    description="Double-clicks at raw screen coordinates (x, y). Fallback only when semantic element cannot be targeted.",
    parameters={
        "type": "object",
        "properties": {
            "x": {"type": "number"},
            "y": {"type": "number"}
        },
        "required": ["x", "y"]
    },
    safety=SafetyLevel.SENSITIVE
)
def double_click(x: float, y: float) -> ToolResult:
    try:
        input_control.double_click(x, y)
        return ToolResult.ok("double_click", x=x, y=y)
    except Exception as e:
        return ToolResult.fail("double_click", "ERROR", str(e))

@tool(
    name="type_text",
    description="Types raw text into the currently focused element. Fallback only when semantic element cannot be targeted with type_into_element.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string"}
        },
        "required": ["text"]
    },
    safety=SafetyLevel.SENSITIVE
)
def type_text(text: str) -> ToolResult:
    try:
        input_control.type_text(text)
        return ToolResult.ok("type_text", text=text)
    except Exception as e:
        return ToolResult.fail("type_text", "ERROR", str(e))

@tool(
    name="press_key",
    description="Presses a single key (e.g., 'return', 'tab', 'escape').",
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string"}
        },
        "required": ["key"]
    },
    safety=SafetyLevel.SAFE
)
def press_key(key: str) -> ToolResult:
    try:
        input_control.press_key(key)
        return ToolResult.ok("press_key", key=key)
    except Exception as e:
        return ToolResult.fail("press_key", "ERROR", str(e))

@tool(
    name="hotkey",
    description="Presses a key combination (e.g., 'command+l').",
    parameters={
        "type": "object",
        "properties": {
            "keys": {"type": "string"}
        },
        "required": ["keys"]
    },
    safety=SafetyLevel.SAFE
)
def hotkey(keys: str) -> ToolResult:
    try:
        key_list = keys.split("+")
        input_control.hotkey(*key_list)
        return ToolResult.ok("hotkey", keys=keys)
    except Exception as e:
        return ToolResult.fail("hotkey", "ERROR", str(e))

@tool(
    name="scroll",
    description="Scrolls by the given amount (positive up, negative down).",
    parameters={
        "type": "object",
        "properties": {
            "amount": {"type": "integer"},
            "x": {"type": "number"},
            "y": {"type": "number"}
        },
        "required": ["amount"]
    },
    safety=SafetyLevel.SAFE
)
def scroll(amount: int, x: float | None = None, y: float | None = None) -> ToolResult:
    try:
        input_control.scroll(amount, x, y)
        return ToolResult.ok("scroll", amount=amount, x=x, y=y)
    except Exception as e:
        return ToolResult.fail("scroll", "ERROR", str(e))
