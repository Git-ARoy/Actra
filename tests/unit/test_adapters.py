"""Unit tests for Universal App Control Layer and Adapter Registry."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from actra.mac.app_adapter import ActionType, NEVER_AUTO_APPROVED, AppAdapter
from actra.mac.adapter_registry import AdapterRegistry, get_adapter_registry
from actra.mac.adapters.safari_adapter import SafariAdapter
from actra.mac.adapters.filesystem_adapter import FilesystemAdapter
from actra.mac.adapters.noop_adapter import NoOpAdapter
from actra.tools.safety import SafetyGate
from actra.models import SafetyLevel, ToolResult


def test_action_types_and_never_auto_approved():
    assert ActionType.EXECUTE in NEVER_AUTO_APPROVED
    assert ActionType.SYSTEM in NEVER_AUTO_APPROVED
    assert ActionType.READ not in NEVER_AUTO_APPROVED
    assert ActionType.NAVIGATE not in NEVER_AUTO_APPROVED
    assert ActionType.INPUT not in NEVER_AUTO_APPROVED
    assert ActionType.MUTATE not in NEVER_AUTO_APPROVED


def test_adapter_registry():
    registry = AdapterRegistry()
    safari = SafariAdapter()
    fs = FilesystemAdapter()
    noop = NoOpAdapter()

    registry.register(safari)
    registry.register(fs)
    registry.register(noop)

    # Lookup by name (case-insensitive)
    assert registry.get("Safari") is safari
    assert registry.get("safari") is safari
    assert registry.get("Filesystem") is fs
    assert registry.get("noop") is noop

    # Lookup by bundle ID
    assert registry.get("com.apple.Safari") is safari
    assert registry.get("com.apple.finder") is fs
    assert registry.get("com.actra.noop") is noop

    # Nonexistent
    assert registry.get("unknown_app") is None

    # List adapters
    adapters = registry.list_adapters()
    assert "Safari" in adapters
    assert "Filesystem" in adapters
    assert "NoOp" in adapters


def test_noop_adapter():
    adapter = NoOpAdapter()
    assert adapter.app_name == "NoOp"
    assert adapter.bundle_id == "com.actra.noop"

    # Discovery
    disco = adapter.discover()
    assert disco["simulated"] is True
    assert disco["app_name"] == "NoOp"

    # Inspect
    insp = adapter.inspect("test_target")
    assert insp["target"] == "test_target"
    assert insp["inspected"] is True

    # Act
    res = adapter.act("ping", ActionType.READ, payload="hello")
    assert isinstance(res, ToolResult)
    assert res.success is True
    assert res.data["action"] == "ping"
    assert res.data["action_type"] == "READ"
    assert res.data["params"] == {"payload": "hello"}

    # Verify
    assert adapter.verify("ping", {}) is True

    # Safety level mapping
    assert adapter.get_safety_level(ActionType.READ) == SafetyLevel.SAFE
    assert adapter.get_safety_level(ActionType.NAVIGATE) == SafetyLevel.SAFE
    assert adapter.get_safety_level(ActionType.MUTATE) == SafetyLevel.SENSITIVE
    assert adapter.get_safety_level(ActionType.EXECUTE) == SafetyLevel.DANGEROUS
    assert adapter.get_safety_level(ActionType.SYSTEM) == SafetyLevel.DANGEROUS


def test_filesystem_adapter_discover_and_inspect(tmp_path: Path):
    adapter = FilesystemAdapter()
    disco = adapter.discover()
    assert "home" in disco
    assert "documents" in disco
    assert "capabilities" in disco

    # Create temporary file
    test_file = tmp_path / "test.txt"
    test_file.write_text("adapter file content")

    insp = adapter.inspect(str(test_file))
    assert insp["success"] is True
    assert insp["data"]["content"] == "adapter file content"


def test_never_auto_approved_safety_enforcement():
    # In 'all' confirmation mode (unattended), standard DANGEROUS actions are auto-approved,
    # but NEVER_AUTO_APPROVED actions (EXECUTE, SYSTEM, safari_do_javascript) MUST require prompt.
    gate = SafetyGate(confirmation_mode="all")

    # Normal dangerous file delete is auto-approved in 'all' mode
    assert gate.check("delete_file", SafetyLevel.DANGEROUS, {"path": "/tmp/safe_tmp.txt"}) is True

    # But safari_do_javascript / EXECUTE is NEVER auto-approved even in 'all' mode
    with patch.object(gate, "_prompt_user", return_value=False) as mock_prompt:
        res = gate.check("safari_do_javascript", SafetyLevel.SENSITIVE, {"javascript": "alert(1)"})
        assert res is False
        mock_prompt.assert_called_once()

    # Explicit ActionType.EXECUTE is also never auto-approved
    with patch.object(gate, "_prompt_user", return_value=False) as mock_prompt:
        res = gate.check("custom_eval", SafetyLevel.SAFE, {"code": "exit()"}, action_type=ActionType.EXECUTE)
        assert res is False
        mock_prompt.assert_called_once()
