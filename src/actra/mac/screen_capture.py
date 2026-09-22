import subprocess
import tempfile
import base64
from pathlib import Path
from PIL import Image

def capture_screen(output_path: Path | None = None) -> Path:
    """Capture full screen to a file. Uses macOS `screencapture -x` (silent).
    If no output_path, saves to a temp file. Returns the path."""
    if output_path is None:
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        output_path = Path(temp_path)
    
    subprocess.run(["screencapture", "-x", str(output_path)], check=True)
    return output_path

def capture_screen_base64() -> str:
    """Capture screen and return as base64-encoded PNG string."""
    temp_path = capture_screen()
    with open(temp_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    temp_path.unlink()
    return encoded_string

def capture_window(window_id: int | None = None, output_path: Path | None = None) -> Path:
    """Capture a specific window. If window_id is None, capture frontmost.
    Uses `screencapture -x -l <window_id>` or `-w` for interactive."""
    if output_path is None:
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        output_path = Path(temp_path)
        
    if window_id is not None:
        subprocess.run(["screencapture", "-x", "-l", str(window_id), str(output_path)], check=True)
    else:
        # Note: -w requires user interaction if not run silently with specific window id
        # As fallback, we do full screen for now.
        subprocess.run(["screencapture", "-x", str(output_path)], check=True)
    
    return output_path

def take_screenshot(output_path: Path | None = None) -> tuple[str, str]:
    """Capture screen and return tuple of (base64_string, file_path_string)."""
    path = capture_screen(output_path)
    with open(path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string, str(path)

def get_window_info() -> dict:
    """Get frontmost application and window information."""
    from actra.mac import apple_events
    front_app = apple_events.get_frontmost_app()
    windows = apple_events.get_app_windows(front_app)
    return {"app": front_app, "windows": windows}
