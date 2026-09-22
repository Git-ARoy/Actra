"""Unit tests for the tool registry."""

import pytest
from actra.models import ToolResult, SafetyLevel
from actra.tools.registry import ToolRegistry, ToolDefinition, tool, _TOOL_DEFINITIONS


class TestToolDecorator:
    def test_decorated_function_is_registered(self):
        """Verify that @tool decorator adds to the global list."""
        initial_count = len(_TOOL_DEFINITIONS)

        @tool(
            name="test_dummy_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}, "required": []},
            safety=SafetyLevel.SAFE,
        )
        def dummy_tool():
            return ToolResult.ok("test_dummy_tool")

        assert len(_TOOL_DEFINITIONS) == initial_count + 1
        assert _TOOL_DEFINITIONS[-1].name == "test_dummy_tool"

    def test_decorated_function_still_callable(self):
        """The wrapped function should still work normally."""
        @tool(
            name="test_callable_tool",
            description="A callable test tool",
            parameters={"type": "object", "properties": {}, "required": []},
        )
        def callable_tool():
            return ToolResult.ok("test_callable_tool", status="ok")

        result = callable_tool()
        assert isinstance(result, ToolResult)
        assert result.success is True


class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        tool_def = ToolDefinition(
            name="my_tool",
            description="Desc",
            parameters={"type": "object", "properties": {}},
            safety=SafetyLevel.SAFE,
            func=lambda: ToolResult.ok("my_tool"),
        )
        registry.register(tool_def)
        assert registry.get("my_tool") is not None
        assert registry.get("my_tool").name == "my_tool"

    def test_get_nonexistent_returns_none(self):
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_list_schemas(self):
        registry = ToolRegistry()
        tool_def = ToolDefinition(
            name="schema_tool",
            description="A tool with schema",
            parameters={"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
            safety=SafetyLevel.SAFE,
            func=lambda x: ToolResult.ok("schema_tool", x=x),
        )
        registry.register(tool_def)
        schemas = registry.list_schemas()
        assert len(schemas) >= 1
        schema = [s for s in schemas if s["name"] == "schema_tool"][0]
        assert schema["description"] == "A tool with schema"
        assert "x" in schema["parameters"]["properties"]

    def test_execute_success(self):
        registry = ToolRegistry()
        tool_def = ToolDefinition(
            name="add_tool",
            description="Adds two numbers",
            parameters={"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}},
            safety=SafetyLevel.SAFE,
            func=lambda a, b: ToolResult.ok("add_tool", sum=a + b),
        )
        registry.register(tool_def)
        result = registry.execute("add_tool", {"a": 2, "b": 3})
        assert result.success is True
        assert result.data["sum"] == 5

    def test_execute_not_found(self):
        registry = ToolRegistry()
        result = registry.execute("nonexistent_tool", {})
        assert result.success is False
        assert result.error.code == "NOT_FOUND"

    def test_execute_handles_exception(self):
        registry = ToolRegistry()

        def bad_func(**kwargs):
            raise RuntimeError("Kaboom!")

        tool_def = ToolDefinition(
            name="bad_tool",
            description="Will fail",
            parameters={"type": "object", "properties": {}},
            safety=SafetyLevel.SAFE,
            func=bad_func,
        )
        registry.register(tool_def)
        result = registry.execute("bad_tool", {})
        assert result.success is False
        assert "Kaboom" in result.error.message

    def test_get_safety_level(self):
        registry = ToolRegistry()
        tool_def = ToolDefinition(
            name="danger_tool",
            description="Dangerous",
            parameters={"type": "object", "properties": {}},
            safety=SafetyLevel.DANGEROUS,
            func=lambda: ToolResult.ok("danger_tool"),
        )
        registry.register(tool_def)
        assert registry.get_safety_level("danger_tool") == SafetyLevel.DANGEROUS
        assert registry.get_safety_level("nonexistent") == SafetyLevel.SAFE
