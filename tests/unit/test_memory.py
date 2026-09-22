"""Unit tests for Actra SQLite persistent memory layer."""

import pytest
import sqlite3
from pathlib import Path
from actra.agent.memory import MemoryStore, get_store, set_default_store, get_preference, set_preference, delete_preference, list_preferences, log_task_outcome, recent_context, get_task_history
from actra.models import Task, TaskStatus, GoalVerificationResult, CheckEvidence


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "test_memory.db"


def test_schema_initialization(temp_db: Path):
    store = MemoryStore(temp_db)
    conn = sqlite3.connect(str(temp_db))
    cur = conn.cursor()
    
    # Check that all tables including reserved ones exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    assert "preferences" in tables
    assert "task_history" in tables
    assert "context_log" in tables
    assert "user_profiles" in tables
    assert "system_alerts" in tables
    assert "skill_library" in tables
    store.close()
    conn.close()


def test_preferences_crud(temp_db: Path):
    store = MemoryStore(temp_db)
    
    # Empty get
    assert store.get_preference("theme") is None
    assert store.get_preference("theme", "dark") == "dark"
    
    # Set and get
    store.set_preference("theme", "light")
    assert store.get_preference("theme") == "light"
    
    # Update
    store.set_preference("theme", "solarized")
    assert store.get_preference("theme") == "solarized"
    
    # Multiple preferences
    store.set_preference("editor", "vscode")
    prefs = store.list_preferences()
    assert prefs == {"editor": "vscode", "theme": "solarized"}
    
    # Delete
    assert store.delete_preference("theme") is True
    assert store.get_preference("theme") is None
    assert store.delete_preference("nonexistent") is False
    
    store.close()


def test_persistence_across_restarts(temp_db: Path):
    # Store in first session
    store1 = MemoryStore(temp_db)
    store1.set_preference("user_name", "Alice")
    store1.log_context_event(None, "system_boot", "Actra booted")
    store1.close()
    
    # Reopen in second session
    store2 = MemoryStore(temp_db)
    assert store2.get_preference("user_name") == "Alice"
    ctx = store2.recent_context(limit=5)
    assert len(ctx) == 1
    assert ctx[0]["event_type"] == "system_boot"
    assert ctx[0]["content"] == "Actra booted"
    store2.close()


def test_log_task_outcome(temp_db: Path):
    store = MemoryStore(temp_db)
    
    task = Task(goal="Search for something in Safari")
    task.mark(TaskStatus.COMPLETED)
    task.step_index = 3
    task.context["final_message"] = "Found results."
    task.verification = GoalVerificationResult(
        verified=True,
        checks=[CheckEvidence(name="safari_running", passed=True, evidence="Safari active")],
        reason="Goal verified successfully"
    )
    
    store.log_task_outcome(task)
    
    history = store.get_task_history(limit=10)
    assert len(history) == 1
    assert history[0]["task_id"] == task.task_id
    assert history[0]["goal"] == "Search for something in Safari"
    assert history[0]["status"] == "COMPLETED"
    assert history[0]["steps_executed"] == 3
    assert history[0]["metadata"]["verification"]["verified"] is True
    assert history[0]["metadata"]["final_message"] == "Found results."
    
    # Check context log was also written
    ctx = store.recent_context(limit=5)
    assert len(ctx) == 1
    assert "COMPLETED" in ctx[0]["content"]
    assert task.task_id[:8] in ctx[0]["content"]
    
    store.close()


def test_global_api_helpers(temp_db: Path):
    store = MemoryStore(temp_db)
    set_default_store(store)
    
    set_preference("default_browser", "Safari")
    assert get_preference("default_browser") == "Safari"
    assert list_preferences() == {"default_browser": "Safari"}
    assert delete_preference("default_browser") is True
    assert get_preference("default_browser") is None
    
    store.close()
