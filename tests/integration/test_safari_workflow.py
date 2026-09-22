"""Integration test for the Safari search workflow using local Gemma 4 12B (MLX).

This test requires:
  - macOS with Safari installed
  - Accessibility permissions granted
  - Local Ollama running with gemma4:12b-mlx
"""

import pytest
from actra.agent import ActraAgent
from actra.models import TaskStatus


class TestSafariWorkflow:
    def test_search_iqoo(self):

        """Milestone 1: 'Open Safari and search for iQOO 15'."""
        agent = ActraAgent()
        task = agent.run("Open Safari and search for iQOO 15")

        assert task.status == TaskStatus.COMPLETED
        assert task.step_index > 0
        assert len(task.tool_calls) > 0

        # Should have called safari-related tools
        tool_names = [tc["tool"] for tc in task.tool_calls]
        safari_tools = [t for t in tool_names if "safari" in t.lower()]
        assert len(safari_tools) > 0, f"Expected safari tools, got: {tool_names}"
