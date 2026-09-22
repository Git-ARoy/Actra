import subprocess

def run_applescript(script: str) -> str:
    """Execute an AppleScript and return stdout."""
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running AppleScript: {e.stderr.strip()}")
        return ""

def open_application(app_name: str) -> bool:
    """Open a macOS application by name."""
    script = f'tell application "{app_name}" to activate'
    try:
        subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def get_frontmost_app() -> str:
    """Get the name of the frontmost application."""
    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
    return run_applescript(script)

def get_app_windows(app_name: str) -> list[dict]:
    """Get window info for an application."""
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            set windowList to every window
            set windowsInfo to {{}}
            repeat with w in windowList
                set end of windowsInfo to (name of w as string)
            end repeat
            return windowsInfo
        end tell
    end tell
    '''
    # Note: A real implementation would parse the AppleScript list output or return JSON
    out = run_applescript(script)
    if not out:
        return []
    # simplified parsing
    names = [name.strip() for name in out.split(',')]
    return [{"name": name} for name in names if name]

def quit_application(app_name: str) -> bool:
    """Quit an application."""
    script = f'tell application "{app_name}" to quit'
    try:
        subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

# Aliases matching tool expectations
activate_application = open_application
close_application = quit_application
get_active_application = get_frontmost_app

def list_running_apps() -> list[str]:
    """List all running applications."""
    script = 'tell application "System Events" to get name of every application process whose background only is false'
    out = run_applescript(script)
    if not out:
        return []
    return [name.strip() for name in out.split(',')]

list_running_applications = list_running_apps
