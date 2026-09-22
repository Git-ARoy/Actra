"""macOS system permissions inspection and setup guidance for Actra."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from ApplicationServices import AXIsProcessTrusted

from actra.mac.apple_events import run_applescript


SAFARI_JS_PERMISSION_INSTRUCTIONS = (
    "To enable Safari webpage text extraction and JavaScript automation:\n"
    "1. Open Safari.\n"
    "2. Open Settings (Cmd+,) → 'Advanced' tab.\n"
    "3. Check 'Show features for web developers' (or 'Show Develop menu in menu bar').\n"
    "4. In the macOS menu bar, click 'Develop' → check 'Allow JavaScript from Apple Events'."
)


def check_accessibility() -> bool:
    """Check if Accessibility permission is granted."""
    return AXIsProcessTrusted()


def check_screen_recording() -> bool:
    """Check if Screen Recording permission is likely granted.
    Try a test screenshot capture and check result."""
    fd, temp_path = tempfile.mkstemp(suffix=".png")
    test_file = Path(temp_path)
    try:
        # Run silent screencapture
        subprocess.run(["screencapture", "-x", str(test_file)], check=True, capture_output=True)
        # Check if file was created and is not empty
        if test_file.exists() and test_file.stat().st_size > 0:
            return True
        return False
    except subprocess.CalledProcessError:
        return False
    finally:
        if test_file.exists():
            test_file.unlink()


def check_safari_js_automation() -> bool:
    """Check if Safari allows JavaScript execution from Apple Events."""
    script = '''
    tell application "Safari"
        if (count of windows) > 0 then
            do JavaScript "1+1" in current tab of front window
        else
            return "no_window"
        end if
    end tell
    '''
    try:
        res = run_applescript(script)
        return True
    except Exception as e:
        err_msg = str(e).lower()
        if "privilege violation" in err_msg or "javascript" in err_msg or "-10004" in err_msg or "-1728" in err_msg or "-2700" in err_msg:
            return False
        # If no window or safari closed, we cannot strictly determine failure
        return True


def check_all_permissions() -> dict[str, bool]:
    """Check all required permissions and return status dict."""
    return {
        "accessibility": check_accessibility(),
        "screen_recording": check_screen_recording(),
        "safari_javascript": check_safari_js_automation(),
    }


def print_permission_guide() -> None:
    """Print instructions for enabling required permissions."""
    print("=== Actra Permissions Guide ===")
    print("Actra requires specific macOS permissions to control the system:")
    print("1. Accessibility: System Settings > Privacy & Security > Accessibility")
    print("   Add and enable your terminal/IDE.")
    print("2. Screen Recording: System Settings > Privacy & Security > Screen Recording")
    print("   Add and enable your terminal/IDE.")
    print("3. Safari Automation: Safari > Settings > Advanced > Show features for web developers")
    print("   Then Develop menu > Allow JavaScript from Apple Events.")
    print("===============================")
