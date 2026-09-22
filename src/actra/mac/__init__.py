"""
macOS native control layer for Actra.
"""

from .apple_events import (
    run_applescript,
    open_application,
    get_frontmost_app,
    get_app_windows,
    quit_application,
    list_running_apps,
    activate_application,
    close_application,
    get_active_application,
    list_running_applications,
)
from .screen_capture import (
    capture_screen,
    capture_screen_base64,
    capture_window,
    take_screenshot,
    get_window_info,
)
from .input_control import (
    click,
    double_click,
    move_mouse,
    type_text,
    press_key,
    hotkey,
    scroll,
)
from .accessibility import (
    check_accessibility_permissions,
    get_frontmost_app_pid,
    inspect_app,
    inspect_ui,
    find_element,
    perform_action,
    click_element,
    type_into_element,
    resolve_element,
)
from .permissions import (
    check_accessibility,
    check_screen_recording,
    check_all_permissions,
    print_permission_guide,
)

__all__ = [
    "run_applescript",
    "open_application",
    "get_frontmost_app",
    "get_app_windows",
    "quit_application",
    "list_running_apps",
    "activate_application",
    "close_application",
    "get_active_application",
    "list_running_applications",
    "capture_screen",
    "capture_screen_base64",
    "capture_window",
    "take_screenshot",
    "get_window_info",
    "click",
    "double_click",
    "move_mouse",
    "type_text",
    "press_key",
    "hotkey",
    "scroll",
    "check_accessibility_permissions",
    "get_frontmost_app_pid",
    "inspect_app",
    "inspect_ui",
    "find_element",
    "perform_action",
    "click_element",
    "type_into_element",
    "resolve_element",
    "check_accessibility",
    "check_screen_recording",
    "check_all_permissions",
    "print_permission_guide",
]


