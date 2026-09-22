"""Unit tests for granular --no-confirm safety modes."""

from unittest.mock import patch
import pytest

from actra.models import SafetyLevel
from actra.tools.safety import SafetyGate
from actra.config import Settings


def test_no_confirm_none_prompts_for_sensitive_and_dangerous():
    """Default mode 'none' requires confirmation for both SENSITIVE and DANGEROUS."""
    gate = SafetyGate(confirmation_mode="none")

    # Safe passes without prompt
    assert gate.check("list_directory", SafetyLevel.SAFE, {"path": "~/Documents"}) is True

    # Sensitive prompts
    with patch.object(gate, "_prompt_user", return_value=True) as mock_prompt:
        assert gate.check("click", SafetyLevel.SENSITIVE, {"x": 10, "y": 20}) is True
        mock_prompt.assert_called_once()

    # Dangerous prompts
    with patch.object(gate, "_prompt_user", return_value=False) as mock_prompt:
        assert gate.check("delete_file", SafetyLevel.DANGEROUS, {"path": "~/Documents/test.txt"}) is False
        mock_prompt.assert_called_once()


def test_no_confirm_sensitive_bypasses_sensitive_only():
    """Mode 'sensitive' auto-approves SENSITIVE tier but prompts for DANGEROUS tier."""
    gate = SafetyGate(confirmation_mode="sensitive")

    # Sensitive executes without prompt
    with patch.object(gate, "_prompt_user") as mock_prompt:
        assert gate.check("click", SafetyLevel.SENSITIVE, {"x": 10, "y": 20}) is True
        mock_prompt.assert_not_called()

    # Dangerous STILL prompts
    with patch.object(gate, "_prompt_user", return_value=True) as mock_prompt:
        assert gate.check("delete_file", SafetyLevel.DANGEROUS, {"path": "~/Documents/test.txt"}) is True
        mock_prompt.assert_called_once()


def test_no_confirm_all_bypasses_all_tiers():
    """Mode 'all' auto-approves both SENSITIVE and DANGEROUS tiers without prompt."""
    gate = SafetyGate(confirmation_mode="all")

    with patch.object(gate, "_prompt_user") as mock_prompt:
        assert gate.check("click", SafetyLevel.SENSITIVE, {"x": 10, "y": 20}) is True
        assert gate.check("delete_file", SafetyLevel.DANGEROUS, {"path": "~/Documents/test.txt"}) is True
        mock_prompt.assert_not_called()


def test_settings_no_confirm_loading(monkeypatch):
    """Verify Settings load correctly reflects environment variable configuration."""
    monkeypatch.setenv("ACTRA_NO_CONFIRM", "sensitive")
    settings = Settings.load()
    assert settings.no_confirm == "sensitive"
    assert settings.require_confirmation is True

    monkeypatch.setenv("ACTRA_NO_CONFIRM", "all")
    settings = Settings.load()
    assert settings.no_confirm == "all"
    assert settings.require_confirmation is False
