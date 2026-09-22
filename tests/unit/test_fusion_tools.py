"""Unit tests for Autodesk Fusion 360 CAD automation tools."""

from pathlib import Path
from unittest.mock import patch
import pytest

from actra.tools.fusion import fusion_create_script, fusion_design_part
from actra.models import ToolResult


def test_fusion_create_script(tmp_path: Path):
    with patch("actra.tools.fusion._get_fusion_scripts_dir", return_value=tmp_path):
        res = fusion_create_script("TestScript", "print('hello fusion')", "Test Description")
        assert res.success is True
        assert (tmp_path / "TestScript" / "TestScript.py").exists()
        assert (tmp_path / "TestScript" / "TestScript.manifest").exists()
        assert "hello fusion" in (tmp_path / "TestScript" / "TestScript.py").read_text()


def test_fusion_design_cup(tmp_path: Path):
    with patch("actra.tools.fusion._get_fusion_scripts_dir", return_value=tmp_path):
        res = fusion_design_part(part_type="cup", radius=4.5, height=12.0, wall_thickness=0.35)
        assert res.success is True
        script_file = tmp_path / "Actra_Cup" / "Actra_Cup.py"
        assert script_file.exists()
        code = script_file.read_text()
        assert "adsk.fusion" in code
        assert "addByCenterRadius" in code
        assert "4.5" in code
        assert "12.0" in code
        assert "shellFeatures" in code
        assert "0.35" in code


def test_fusion_design_box(tmp_path: Path):
    with patch("actra.tools.fusion._get_fusion_scripts_dir", return_value=tmp_path):
        res = fusion_design_part(part_type="box", radius=5.0, height=8.0)
        assert res.success is True
        script_file = tmp_path / "Actra_Box" / "Actra_Box.py"
        assert script_file.exists()
        code = script_file.read_text()
        assert "addTwoPointRectangle" in code


def test_fusion_design_unsupported():
    res = fusion_design_part(part_type="unsupported_gearbox")
    assert res.success is False
    assert res.error.code == "UNSUPPORTED_TYPE"
