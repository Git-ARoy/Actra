"""Level 2 Verification Regression Suite for Actra.

Covers 12 canonical tasks across all core tool domains:
- Browser (Safari search, URL navigation)
- Filesystem (create folder, create/read file, copy file, move file)
- Application Management (launch app, window inspection)
- Spreadsheet (create workbook, append table row)
- Semantic GUI Input (inspect UI, semantic element action)
- Safety Gating (dangerous delete refusal)

Can be executed as:
  pytest tests/test_level2_regression.py -v
or as a standalone CLI runner:
  python tests/test_level2_regression.py
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from actra.models import Task, TaskStatus, SafetyLevel, ToolResult
from actra.agent.agent import ActraAgent
from actra.agent.verifier import Verifier
from actra.config import Settings
from actra.tools.registry import ToolRegistry
from actra.tools.safety import SafetyGate


@pytest.fixture
def regression_env():
    """Create isolated sandbox directory for filesystem and spreadsheet regression tests."""
    temp_dir = tempfile.mkdtemp(prefix="actra_l2_regression_")
    yield Path(temp_dir)
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


class TestLevel2RegressionSuite:
    """12-test canonical regression suite with Level 2 goal verification."""

    def test_01_safari_search_l2(self):
        """Domain: Browser — Verify Safari search and goal verification."""
        verifier = Verifier()
        task = Task(goal="Open Safari and search for iQOO 15")
        task.tool_calls = [
            {"tool": "safari_open", "arguments": {}, "result": {"success": True, "tool": "safari_open"}},
            {"tool": "safari_search", "arguments": {"query": "iQOO 15"}, "result": {"success": True, "tool": "safari_search", "data": {"url": "https://www.google.com/search?q=iQOO+15"}}}
        ]

        with patch("actra.mac.apple_events.list_running_apps", return_value=["Safari", "Finder"]):
            with patch("actra.mac.apple_events.run_applescript", side_effect=["https://www.google.com/search?q=iQOO+15", "iQOO 15 - Google Search"]):
                res = verifier.verify_goal(task)
                assert res.verified is True
                assert any(c.name == "safari_process_active" and c.passed for c in res.checks)
                assert any(c.name == "safari_url_loaded" and c.passed for c in res.checks)

    def test_02_safari_navigate_l2(self):
        """Domain: Browser — Verify Safari URL navigation."""
        verifier = Verifier()
        task = Task(goal="Open Safari and navigate to https://www.apple.com")
        task.tool_calls = [
            {"tool": "safari_open", "arguments": {}, "result": {"success": True, "tool": "safari_open"}},
            {"tool": "safari_navigate", "arguments": {"url": "https://www.apple.com"}, "result": {"success": True, "tool": "safari_navigate", "data": {"url": "https://www.apple.com"}}}
        ]

        with patch("actra.mac.apple_events.list_running_apps", return_value=["Safari"]):
            with patch("actra.mac.apple_events.run_applescript", side_effect=["https://www.apple.com", "Apple"]):
                res = verifier.verify_goal(task)
                assert res.verified is True

    def test_03_create_folder_l2(self, regression_env):
        """Domain: Filesystem — Verify folder creation on disk."""
        verifier = Verifier()
        folder_path = regression_env / "TestFolder"
        task = Task(goal=f"Create a folder at {folder_path}")

        # Execute tool
        from actra.tools.filesystem import create_folder
        tool_res = create_folder(str(folder_path))
        assert tool_res.success is True
        task.tool_calls.append({"tool": "create_folder", "arguments": {"path": str(folder_path)}, "result": tool_res.model_dump()})

        res = verifier.verify_goal(task)
        assert res.verified is True
        assert folder_path.exists() and folder_path.is_dir()

    def test_04_create_and_read_file_l2(self, regression_env):
        """Domain: Filesystem — Verify file writing and content verification."""
        verifier = Verifier()
        file_path = regression_env / "notes.txt"
        task = Task(goal=f"Create a file at {file_path} with content 'Regression Pass'")

        from actra.tools.filesystem import create_file, read_file
        w_res = create_file(str(file_path), "Regression Pass")
        r_res = read_file(str(file_path))

        task.tool_calls.append({"tool": "create_file", "arguments": {"path": str(file_path)}, "result": w_res.model_dump()})
        task.tool_calls.append({"tool": "read_file", "arguments": {"path": str(file_path)}, "result": r_res.model_dump()})

        res = verifier.verify_goal(task)
        assert res.verified is True
        assert file_path.read_text() == "Regression Pass"

    def test_05_copy_file_with_overwrite_protection_l2(self, regression_env):
        """Domain: Filesystem — Verify file copying and overwrite safety."""
        verifier = Verifier()
        src_path = regression_env / "original.txt"
        dst_path = regression_env / "backup.txt"
        src_path.write_text("Source Data")

        from actra.tools.filesystem import copy_file
        # First copy succeeds
        c_res = copy_file(str(src_path), str(dst_path), overwrite=False)
        assert c_res.success is True

        # Second copy without overwrite fails
        fail_res = copy_file(str(src_path), str(dst_path), overwrite=False)
        assert fail_res.success is False
        assert fail_res.error.code == "ALREADY_EXISTS"

        task = Task(goal=f"Copy file {src_path} to {dst_path}")
        task.tool_calls.append({"tool": "copy_file", "arguments": {"source": str(src_path), "destination": str(dst_path)}, "result": c_res.model_dump()})

        res = verifier.verify_goal(task)
        assert res.verified is True
        assert dst_path.exists()

    def test_06_move_file_l2(self, regression_env):
        """Domain: Filesystem — Verify file renaming/moving."""
        verifier = Verifier()
        src_path = regression_env / "to_move.txt"
        dst_path = regression_env / "moved.txt"
        src_path.write_text("Moving Content")

        from actra.tools.filesystem import move_file
        m_res = move_file(str(src_path), str(dst_path), overwrite=False)
        assert m_res.success is True
        assert not src_path.exists()
        assert dst_path.exists()

        task = Task(goal=f"Move {src_path} to {dst_path}")
        task.tool_calls.append({"tool": "move_file", "arguments": {"source": str(src_path), "destination": str(dst_path)}, "result": m_res.model_dump()})

        res = verifier.verify_goal(task)
        assert res.verified is True

    def test_07_app_lifecycle_launch_l2(self):
        """Domain: Application Management — Verify application launch detection."""
        verifier = Verifier()
        task = Task(goal="Open Calculator application")
        task.tool_calls = [
            {"tool": "open_app", "arguments": {"app_name": "Calculator"}, "result": {"success": True, "tool": "open_app"}}
        ]

        with patch("actra.mac.apple_events.list_running_apps", return_value=["Calculator", "Finder"]):
            res = verifier.verify_goal(task)
            assert res.verified is True
            assert any(c.name == "application_running_check" and c.passed for c in res.checks)

    def test_08_window_observation_l2(self):
        """Domain: Observation — Verify active application and window metadata."""
        from actra.tools.observation import get_window_info
        with patch("actra.mac.screen_capture.get_window_info", return_value={"title": "Actra Project", "app": "Visual Studio Code"}):
            res = get_window_info()
            assert res.success is True
            assert res.data["info"]["app"] == "Visual Studio Code"

    def test_09_spreadsheet_creation_l2(self, regression_env):
        """Domain: Spreadsheet — Verify workbook creation on disk."""
        verifier = Verifier()
        sheet_path = regression_env / "finances.xlsx"
        task = Task(goal=f"Create a spreadsheet at {sheet_path}")

        from actra.tools.spreadsheet import create_workbook
        tool_res = create_workbook(str(sheet_path), headers=["Category", "Amount"])
        assert tool_res.success is True

        task.tool_calls.append({"tool": "create_workbook", "arguments": {"path": str(sheet_path)}, "result": tool_res.model_dump()})

        res = verifier.verify_goal(task)
        assert res.verified is True
        assert sheet_path.exists()

    def test_10_spreadsheet_append_row_l2(self, regression_env):
        """Domain: Spreadsheet — Verify row appending to table."""
        sheet_path = regression_env / "expenses.xlsx"
        from actra.tools.spreadsheet import create_workbook, append_table_row, read_sheet
        create_workbook(str(sheet_path), headers=["Date", "Item", "Amount"])

        res_append = append_table_row(str(sheet_path), values={"Date": "2026-09-14", "Item": "Domain Hosting", "Amount": "19.99"})
        assert res_append.success is True

        read_res = read_sheet(str(sheet_path))
        assert read_res.success is True
        rows = read_res.data.get("rows", [])
        assert len(rows) >= 2  # header + data

    def test_11_semantic_gui_element_action_l2(self):
        """Domain: GUI Input — Verify semantic element resolution and click."""
        from actra.mac import accessibility
        from actra.tools.computer import click_element
        accessibility._ELEMENT_CACHE.clear()

        mock_btn = MagicMock()
        accessibility._ELEMENT_CACHE["@e100"] = {
            "element": mock_btn,
            "pid": 555,
            "path": [0, 1],
            "node": {"id": "@e100", "role": "AXButton", "title": "Submit Button"}
        }

        with patch("actra.mac.accessibility.AXUIElementPerformAction", return_value=0):
            res = click_element("@e100")
            assert res.success is True
            assert res.data["element_ref"] == "@e100"

    def test_12_safety_policy_gating_l2(self, regression_env):
        """Domain: Safety — Verify dangerous deletion prompt and denial safety."""
        gate = SafetyGate(confirmation_mode="none")
        protected_dir = regression_env / "ImportantData"
        protected_dir.mkdir()

        # Simulate user denying dangerous delete
        with patch.object(gate, "_prompt_user", return_value=False) as mock_prompt:
            allowed = gate.check("delete_file", SafetyLevel.DANGEROUS, {"path": str(protected_dir)})
            assert allowed is False
            mock_prompt.assert_called_once()
            # Directory must remain intact on disk
            assert protected_dir.exists()


def run_standalone_regression():
    """Run regression tests as a standalone CLI runner and print summary report."""
    print("=" * 65)
    print("RUNNING ACTRA LEVEL 2 VERIFICATION REGRESSION SUITE (12 TESTS)")
    print("=" * 65)

    suite = TestLevel2RegressionSuite()
    tests = [
        ("1. Browser: Safari Search", suite.test_01_safari_search_l2),
        ("2. Browser: Safari Navigate", suite.test_02_safari_navigate_l2),
        ("3. Filesystem: Create Folder", lambda: suite.test_03_create_folder_l2(Path(tempfile.mkdtemp()))),
        ("4. Filesystem: Create & Read File", lambda: suite.test_04_create_and_read_file_l2(Path(tempfile.mkdtemp()))),
        ("5. Filesystem: Copy & Overwrite Protect", lambda: suite.test_05_copy_file_with_overwrite_protection_l2(Path(tempfile.mkdtemp()))),
        ("6. Filesystem: Move File", lambda: suite.test_06_move_file_l2(Path(tempfile.mkdtemp()))),
        ("7. App Mgmt: Application Launch", suite.test_07_app_lifecycle_launch_l2),
        ("8. Observation: Window Info", suite.test_08_window_observation_l2),
        ("9. Spreadsheet: Create Workbook", lambda: suite.test_09_spreadsheet_creation_l2(Path(tempfile.mkdtemp()))),
        ("10. Spreadsheet: Append Table Row", lambda: suite.test_10_spreadsheet_append_row_l2(Path(tempfile.mkdtemp()))),
        ("11. GUI: Semantic Element Action", suite.test_11_semantic_gui_element_action_l2),
        ("12. Safety: Dangerous Policy Gating", lambda: suite.test_12_safety_policy_gating_l2(Path(tempfile.mkdtemp()))),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print(f"✅ {name:<45} [PASSED]")
            passed += 1
        except Exception as e:
            print(f"❌ {name:<45} [FAILED: {e}]")
            failed += 1

    print("=" * 65)
    print(f"SUMMARY: {passed} PASSED | {failed} FAILED | TOTAL: {len(tests)}")
    print("=" * 65)
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_standalone_regression()
    sys.exit(0 if success else 1)
