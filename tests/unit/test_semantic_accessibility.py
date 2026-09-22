"""Unit tests for semantic accessibility actions and element resolution."""

from unittest.mock import MagicMock, patch
import pytest

from actra.models import SafetyLevel, ToolResult
from actra.mac import accessibility
from actra.tools.registry import ToolRegistry
from actra.tools.computer import click_element, type_into_element


def test_element_cache_and_resolution():
    """Test assigning IDs and resolving element references."""
    accessibility._ELEMENT_CACHE.clear()

    # Simulate a populated cache
    mock_elem1 = MagicMock()
    mock_elem2 = MagicMock()

    accessibility._ELEMENT_CACHE["@e1"] = {
        "element": mock_elem1,
        "pid": 1234,
        "path": [0],
        "node": {"id": "@e1", "role": "AXWindow", "title": "Main Window"}
    }
    accessibility._ELEMENT_CACHE["@e2"] = {
        "element": mock_elem2,
        "pid": 1234,
        "path": [0, 1],
        "node": {"id": "@e2", "role": "AXButton", "title": "Submit", "position": {"x": 100, "y": 200}, "size": {"width": 50, "height": 30}}
    }

    # 1. Resolve by @e2 ID
    res = accessibility.resolve_element("@e2")
    assert res is not None
    elem, node = res
    assert elem is mock_elem2
    assert node["title"] == "Submit"

    # 2. Resolve without @ prefix
    res = accessibility.resolve_element("e2")
    assert res is not None
    assert res[0] is mock_elem2

    # 3. Resolve by numeric id
    res = accessibility.resolve_element("2")
    assert res is not None
    assert res[0] is mock_elem2

    # 4. Resolve by role and title
    res = accessibility.resolve_element("button:Submit")
    assert res is not None
    assert res[0] is mock_elem2

    # 5. Resolve by title only
    res = accessibility.resolve_element("Submit")
    assert res is not None
    assert res[0] is mock_elem2


def test_click_element_tool():
    """Test click_element tool executing AX action."""
    accessibility._ELEMENT_CACHE.clear()
    mock_elem = MagicMock()

    accessibility._ELEMENT_CACHE["@e10"] = {
        "element": mock_elem,
        "pid": 999,
        "path": [0],
        "node": {"id": "@e10", "role": "AXButton", "title": "Save"}
    }

    with patch("actra.mac.accessibility.AXUIElementPerformAction", return_value=0):
        res = click_element("@e10")
        assert res.success is True
        assert res.tool == "click_element"
        assert res.data["element_ref"] == "@e10"


def test_click_element_fallback_to_coordinates():
    """Test click_element falling back to center coordinate click when AX action fails."""
    accessibility._ELEMENT_CACHE.clear()
    mock_elem = MagicMock()

    accessibility._ELEMENT_CACHE["@e11"] = {
        "element": mock_elem,
        "pid": 999,
        "path": [0],
        "node": {
            "id": "@e11",
            "role": "AXButton",
            "title": "Save",
            "position": {"x": 200.0, "y": 100.0},
            "size": {"width": 80.0, "height": 40.0}
        }
    }

    with patch("actra.mac.accessibility.AXUIElementPerformAction", return_value=-25204):  # kAXErrorActionUnsupported
        with patch("actra.mac.input_control.click") as mock_click:
            res = click_element("@e11")
            assert res.success is True
            mock_click.assert_called_once_with(240.0, 120.0)


def test_type_into_element_tool():
    """Test type_into_element setting text directly or typing."""
    accessibility._ELEMENT_CACHE.clear()
    mock_elem = MagicMock()

    accessibility._ELEMENT_CACHE["@e12"] = {
        "element": mock_elem,
        "pid": 999,
        "path": [0],
        "node": {"id": "@e12", "role": "AXTextField", "title": "Search"}
    }

    with patch("actra.mac.accessibility.AXUIElementSetAttributeValue", return_value=0):
        res = type_into_element("@e12", "hello world")
        assert res.success is True
        assert res.tool == "type_into_element"


def test_tool_registry_has_semantic_tools():
    """Verify tool registry includes click_element and type_into_element at SENSITIVE tier."""
    registry = ToolRegistry()
    registry.register_all_defaults()

    click_elem_def = registry.get("click_element")
    assert click_elem_def is not None
    assert click_elem_def.safety == SafetyLevel.SENSITIVE

    type_elem_def = registry.get("type_into_element")
    assert type_elem_def is not None
    assert type_elem_def.safety == SafetyLevel.SENSITIVE
