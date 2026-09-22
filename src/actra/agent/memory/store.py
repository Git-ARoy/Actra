"""SQLite-based persistent memory store for Actra."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from actra.models import Task


class MemoryStore:
    """Manages SQLite persistent storage for preferences, history, and context."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None:
            self._db_path = Path.home() / ".actra" / "memory.db"
        elif isinstance(db_path, str):
            self._db_path = Path(db_path).expanduser()
        else:
            self._db_path = db_path.expanduser()

        if str(self._db_path) != ":memory:":
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Create tables if they do not exist."""
        with self._conn:
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS task_history (
                    task_id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    steps_executed INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS context_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    event_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (task_id) REFERENCES task_history(task_id)
                );

                -- Reserved tables for future phases (Phase 4, 5, 6)
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    display_name TEXT,
                    voice_signature BLOB,
                    trust_level TEXT DEFAULT 'OWNER',
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS system_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    resolved_at TEXT
                );

                CREATE TABLE IF NOT EXISTS skill_library (
                    skill_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    learned_from_task TEXT,
                    recipe TEXT,
                    success_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
            """)

    # ------------------------------------------------------------------
    # Preferences API
    # ------------------------------------------------------------------

    def get_preference(self, key: str, default: str | None = None) -> str | None:
        """Retrieve a stored preference value."""
        cur = self._conn.execute(
            "SELECT value FROM preferences WHERE key = ?", (key,)
        )
        row = cur.fetchone()
        if row is not None:
            return str(row["value"])
        return default

    def set_preference(self, key: str, value: str) -> None:
        """Store or update a preference value."""
        now = datetime.now(timezone.utc).isoformat()
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO preferences (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (key, str(value), now),
            )

    def delete_preference(self, key: str) -> bool:
        """Delete a preference. Returns True if existed and deleted."""
        with self._conn:
            cur = self._conn.execute(
                "DELETE FROM preferences WHERE key = ?", (key,)
            )
            return cur.rowcount > 0

    def list_preferences(self) -> dict[str, str]:
        """Return all stored preferences as a key-value dictionary."""
        cur = self._conn.execute("SELECT key, value FROM preferences ORDER BY key ASC")
        return {row["key"]: row["value"] for row in cur.fetchall()}

    # ------------------------------------------------------------------
    # Task History & Outcome API
    # ------------------------------------------------------------------

    def log_task_outcome(self, task: Task) -> None:
        """Record the outcome of a completed or failed task."""
        created_str = task.created_at.isoformat() if task.created_at else datetime.now(timezone.utc).isoformat()
        completed_str = task.completed_at.isoformat() if task.completed_at else datetime.now(timezone.utc).isoformat()

        meta = {
            "retries": task.retries,
            "verification": task.verification.model_dump() if task.verification else None,
            "context_keys": list(task.context.keys()),
            "tool_call_count": len(task.tool_calls),
            "final_message": task.context.get("final_message"),
            "block_reason": task.block_reason,
        }

        with self._conn:
            self._conn.execute(
                """
                INSERT INTO task_history (
                    task_id, goal, status, steps_executed, error_message, created_at, completed_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    status = excluded.status,
                    steps_executed = excluded.steps_executed,
                    error_message = excluded.error_message,
                    completed_at = excluded.completed_at,
                    metadata = excluded.metadata
                """,
                (
                    task.task_id,
                    task.goal,
                    task.status.value,
                    task.step_index,
                    task.error_message,
                    created_str,
                    completed_str,
                    json.dumps(meta),
                ),
            )

            summary = f"Task [{task.task_id[:8]}] finished with status {task.status.value}. Goal: '{task.goal}'"
            if task.error_message:
                summary += f" | Error: {task.error_message}"
            self._conn.execute(
                """
                INSERT INTO context_log (task_id, event_type, content, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (task.task_id, "task_outcome", summary, completed_str),
            )

    def log_context_event(self, task_id: str | None, event_type: str, content: str) -> None:
        """Log a generic context event."""
        now = datetime.now(timezone.utc).isoformat()
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO context_log (task_id, event_type, content, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (task_id, event_type, content, now),
            )

    def recent_context(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve recent context log entries ordered by recency."""
        cur = self._conn.execute(
            """
            SELECT id, task_id, event_type, content, timestamp
            FROM context_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        return [
            {
                "id": row["id"],
                "task_id": row["task_id"],
                "event_type": row["event_type"],
                "content": row["content"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]

    def get_task_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieve recent task history entries."""
        cur = self._conn.execute(
            """
            SELECT task_id, goal, status, steps_executed, error_message, created_at, completed_at, metadata
            FROM task_history
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        result = []
        for row in cur.fetchall():
            meta = {}
            if row["metadata"]:
                try:
                    meta = json.loads(row["metadata"])
                except Exception:
                    pass
            result.append({
                "task_id": row["task_id"],
                "goal": row["goal"],
                "status": row["status"],
                "steps_executed": row["steps_executed"],
                "error_message": row["error_message"],
                "created_at": row["created_at"],
                "completed_at": row["completed_at"],
                "metadata": meta,
            })
        return result

    def close(self) -> None:
        """Close database connection."""
        self._conn.close()
