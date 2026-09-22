"""Filesystem & Finder Application Adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from actra.mac.app_adapter import ActionType, AppAdapter
from actra.models import ToolResult
from actra.tools import filesystem


class FilesystemAdapter(AppAdapter):
    """Adapter for managing macOS filesystem and Finder actions."""

    @property
    def app_name(self) -> str:
        return "Filesystem"

    @property
    def bundle_id(self) -> str:
        return "com.apple.finder"

    def discover(self) -> dict[str, Any]:
        return {
            "app_name": self.app_name,
            "bundle_id": self.bundle_id,
            "home": str(Path.home()),
            "documents": str(Path.home() / "Documents"),
            "downloads": str(Path.home() / "Downloads"),
            "desktop": str(Path.home() / "Desktop"),
            "capabilities": [
                "find_file", "list_directory", "create_folder", "create_file",
                "move_file", "copy_file", "open_file", "read_file", "write_file", "delete_file"
            ],
        }

    def inspect(self, target: str | None = None) -> dict[str, Any]:
        if not target:
            return self.discover()
        p = Path(target).expanduser()
        if not p.exists():
            return {"path": target, "exists": False}
        if p.is_dir():
            res = filesystem.list_directory(path=str(p))
            return res.model_dump()
        else:
            res = filesystem.read_file(path=str(p))
            return res.model_dump()

    def act(self, action: str, action_type: ActionType, **kwargs: Any) -> ToolResult:
        action_clean = action.lower().strip()
        if action_clean == "find_file":
            return filesystem.find_file(directory=kwargs.get("directory", ""), pattern=kwargs.get("pattern", "*"))
        elif action_clean == "list_directory":
            return filesystem.list_directory(path=kwargs.get("path", ""))
        elif action_clean == "create_folder":
            return filesystem.create_folder(path=kwargs.get("path", ""))
        elif action_clean == "create_file":
            return filesystem.create_file(path=kwargs.get("path", ""), content=kwargs.get("content", ""))
        elif action_clean == "move_file":
            return filesystem.move_file(source=kwargs.get("source", ""), destination=kwargs.get("destination", ""), overwrite=kwargs.get("overwrite", False))
        elif action_clean == "copy_file":
            return filesystem.copy_file(source=kwargs.get("source", ""), destination=kwargs.get("destination", ""), overwrite=kwargs.get("overwrite", False))
        elif action_clean == "open_file":
            return filesystem.open_file(path=kwargs.get("path", ""))
        elif action_clean == "read_file":
            return filesystem.read_file(path=kwargs.get("path", ""), max_chars=kwargs.get("max_chars", 20000))
        elif action_clean == "write_file":
            return filesystem.write_file(path=kwargs.get("path", ""), content=kwargs.get("content", ""))
        elif action_clean == "delete_file":
            return filesystem.delete_file(path=kwargs.get("path", ""))
        else:
            return ToolResult.fail("filesystem_adapter", "UNKNOWN_ACTION", f"Unknown action '{action}' for Filesystem")

    def verify(self, action: str, expected: dict[str, Any]) -> bool:
        if "path_exists" in expected:
            p = Path(expected["path_exists"]).expanduser()
            if not p.exists():
                return False
        if "path_is_dir" in expected:
            p = Path(expected["path_is_dir"]).expanduser()
            if not (p.exists() and p.is_dir()):
                return False
        if "path_deleted" in expected:
            p = Path(expected["path_deleted"]).expanduser()
            if p.exists():
                return False
        return True
