import functools
from typing import Callable, Any
from actra.models import ToolResult, SafetyLevel

class ToolDefinition:
    def __init__(self, name: str, description: str, parameters: dict, safety: SafetyLevel, func: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.safety = safety
        self.func = func

_TOOL_DEFINITIONS: list[ToolDefinition] = []

def tool(
    name: str,
    description: str,
    parameters: dict,
    safety: SafetyLevel = SafetyLevel.SAFE,
):
    """Decorator to register a function as a tool."""
    def decorator(func: Callable):
        tool_def = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            safety=safety,
            func=func
        )
        _TOOL_DEFINITIONS.append(tool_def)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        
    def register_all_defaults(self) -> None:
        """Register all default built-in tools."""
        from actra.tools import (  # noqa: F401
            applications,
            browser,
            computer,
            filesystem,
            fusion,
            observation,
            spreadsheet,
        )
        for tool_def in _TOOL_DEFINITIONS:
            self.register(tool_def)
            
    def register(self, tool_def: ToolDefinition) -> None:

        """Register a single ToolDefinition."""
        self._tools[tool_def.name] = tool_def
        
    def get(self, name: str) -> ToolDefinition | None:
        """Get a tool definition by name."""
        return self._tools.get(name)
        
    def list_schemas(self) -> list[dict]:
        """Returns LLM-compatible tool schemas."""
        schemas = []
        for tool_def in self._tools.values():
            schemas.append({
                "name": tool_def.name,
                "description": tool_def.description,
                "parameters": tool_def.parameters
            })
        return schemas
        
    def execute(self, name: str, arguments: dict) -> ToolResult:
        """Execute a tool by name with arguments."""
        tool_def = self.get(name)
        if not tool_def:
            return ToolResult.fail(name, "NOT_FOUND", f"Tool '{name}' not found.")
        try:
            result = tool_def.func(**arguments)
            if isinstance(result, ToolResult):
                return result
            return ToolResult.ok(name, result=result)
        except Exception as e:
            return ToolResult.fail(name, "EXECUTION_ERROR", str(e))
            
    def get_safety_level(self, name: str) -> SafetyLevel:
        """Get safety level for a tool by name."""
        tool_def = self.get(name)
        if tool_def:
            return tool_def.safety
        return SafetyLevel.SAFE
