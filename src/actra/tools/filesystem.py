import shutil
import subprocess
from pathlib import Path
from actra.models import ToolResult, SafetyLevel
from .registry import tool

@tool(
    name="find_file",
    description="Searches for files matching pattern (glob). Returns list of matches.",
    parameters={
        "type": "object",
        "properties": {
            "directory": {"type": "string"},
            "pattern": {"type": "string"}
        },
        "required": ["directory", "pattern"]
    },
    safety=SafetyLevel.SAFE
)
def find_file(directory: str, pattern: str) -> ToolResult:
    try:
        dir_path = Path(directory).expanduser()
        if not dir_path.exists() or not dir_path.is_dir():
            return ToolResult.fail("find_file", "NOT_FOUND", f"Directory not found: {directory}")
        
        matches = list(dir_path.rglob(pattern))
        str_matches = [str(p) for p in matches]
        return ToolResult.ok("find_file", matches=str_matches)
    except Exception as e:
        return ToolResult.fail("find_file", "ERROR", str(e))

@tool(
    name="list_directory",
    description="Lists contents of a directory with type/size info.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"}
        },
        "required": ["path"]
    },
    safety=SafetyLevel.SAFE
)
def list_directory(path: str) -> ToolResult:
    try:
        dir_path = Path(path).expanduser()
        if not dir_path.exists() or not dir_path.is_dir():
            return ToolResult.fail("list_directory", "NOT_FOUND", f"Directory not found: {path}")
            
        contents = []
        for item in dir_path.iterdir():
            stats = item.stat()
            contents.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": stats.st_size
            })
        return ToolResult.ok("list_directory", contents=contents)
    except Exception as e:
        return ToolResult.fail("list_directory", "ERROR", str(e))

@tool(
    name="create_folder",
    description="Creates a directory.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"}
        },
        "required": ["path"]
    },
    safety=SafetyLevel.SAFE
)
def create_folder(path: str) -> ToolResult:
    try:
        dir_path = Path(path).expanduser()
        dir_path.mkdir(parents=True, exist_ok=True)
        return ToolResult.ok("create_folder", path=str(dir_path))
    except Exception as e:
        return ToolResult.fail("create_folder", "ERROR", str(e))

@tool(
    name="create_file",
    description="Creates a file with optional content.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"}
        },
        "required": ["path"]
    },
    safety=SafetyLevel.SENSITIVE
)
def create_file(path: str, content: str = "") -> ToolResult:
    try:
        file_path = Path(path).expanduser()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return ToolResult.ok("create_file", path=str(file_path))
    except Exception as e:
        return ToolResult.fail("create_file", "ERROR", str(e))

@tool(
    name="move_file",
    description="Moves or renames a file or directory. Fails if destination exists unless overwrite=True.",
    parameters={
        "type": "object",
        "properties": {
            "source": {"type": "string"},
            "destination": {"type": "string"},
            "overwrite": {"type": "boolean", "description": "Overwrite destination if it already exists (default false)"}
        },
        "required": ["source", "destination"]
    },
    safety=SafetyLevel.SENSITIVE
)
def move_file(source: str, destination: str, overwrite: bool = False) -> ToolResult:
    try:
        src_path = Path(source).expanduser()
        dst_path = Path(destination).expanduser()
        if not src_path.exists():
            return ToolResult.fail("move_file", "NOT_FOUND", f"Source not found: {source}")
        if dst_path.exists() and not overwrite:
            return ToolResult.fail("move_file", "ALREADY_EXISTS", f"Destination already exists: {destination}. Pass overwrite=True to overwrite.")
        if dst_path.exists() and overwrite:
            if dst_path.is_dir():
                shutil.rmtree(dst_path)
            else:
                dst_path.unlink()
        shutil.move(str(src_path), str(dst_path))
        return ToolResult.ok("move_file", source=str(src_path), destination=str(dst_path), overwritten=overwrite)
    except Exception as e:
        return ToolResult.fail("move_file", "ERROR", str(e))

@tool(
    name="copy_file",
    description="Copies a file or directory. Fails if destination exists unless overwrite=True.",
    parameters={
        "type": "object",
        "properties": {
            "source": {"type": "string"},
            "destination": {"type": "string"},
            "overwrite": {"type": "boolean", "description": "Overwrite destination if it already exists (default false)"}
        },
        "required": ["source", "destination"]
    },
    safety=SafetyLevel.SAFE
)
def copy_file(source: str, destination: str, overwrite: bool = False) -> ToolResult:
    try:
        src_path = Path(source).expanduser()
        dst_path = Path(destination).expanduser()
        if not src_path.exists():
            return ToolResult.fail("copy_file", "NOT_FOUND", f"Source not found: {source}")
        if dst_path.exists() and not overwrite:
            return ToolResult.fail("copy_file", "ALREADY_EXISTS", f"Destination already exists: {destination}. Pass overwrite=True to overwrite.")
        if src_path.is_dir():
            shutil.copytree(str(src_path), str(dst_path), dirs_exist_ok=overwrite)
        else:
            shutil.copy2(str(src_path), str(dst_path))
        return ToolResult.ok("copy_file", source=str(src_path), destination=str(dst_path), overwritten=overwrite)
    except Exception as e:
        return ToolResult.fail("copy_file", "ERROR", str(e))


@tool(
    name="open_file",
    description="Opens a file with the default macOS app.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"}
        },
        "required": ["path"]
    },
    safety=SafetyLevel.SAFE
)
def open_file(path: str) -> ToolResult:
    try:
        file_path = Path(path).expanduser()
        if not file_path.exists():
            return ToolResult.fail("open_file", "NOT_FOUND", f"File not found: {path}")
        subprocess.run(["open", str(file_path)], check=True)
        return ToolResult.ok("open_file", path=str(file_path))
    except Exception as e:
        return ToolResult.fail("open_file", "ERROR", str(e))

@tool(
    name="read_file",
    description="Reads the text content of a file.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "max_chars": {"type": "integer"}
        },
        "required": ["path"]
    },
    safety=SafetyLevel.SAFE
)
def read_file(path: str, max_chars: int = 20000) -> ToolResult:
    try:
        file_path = Path(path).expanduser()
        if not file_path.exists() or not file_path.is_file():
            return ToolResult.fail("read_file", "NOT_FOUND", f"File not found: {path}")
        text = file_path.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n... [truncated to {max_chars} chars]"
        return ToolResult.ok("read_file", content=text, length=len(text))
    except Exception as e:
        return ToolResult.fail("read_file", "ERROR", str(e))

@tool(
    name="write_file",
    description="Overwrites or creates a file with the given content.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"}
        },
        "required": ["path", "content"]
    },
    safety=SafetyLevel.SENSITIVE
)
def write_file(path: str, content: str) -> ToolResult:
    try:
        file_path = Path(path).expanduser()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return ToolResult.ok("write_file", path=str(file_path), bytes_written=len(content.encode("utf-8")))
    except Exception as e:
        return ToolResult.fail("write_file", "ERROR", str(e))

@tool(
    name="delete_file",
    description="Deletes a file or directory.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"}
        },
        "required": ["path"]
    },
    safety=SafetyLevel.DANGEROUS
)
def delete_file(path: str) -> ToolResult:
    try:
        target_path = Path(path).expanduser()
        if not target_path.exists():
            return ToolResult.fail("delete_file", "NOT_FOUND", f"Path not found: {path}")
        if target_path.is_dir():
            shutil.rmtree(target_path)
        else:
            target_path.unlink()
        return ToolResult.ok("delete_file", path=str(target_path))
    except Exception as e:
        return ToolResult.fail("delete_file", "ERROR", str(e))


