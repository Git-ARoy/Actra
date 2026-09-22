"""macOS Accessibility tree inspection and semantic interaction using pyobjc."""

from __future__ import annotations

import re
from typing import Any

import AppKit
from ApplicationServices import (
    AXUIElementCreateApplication,
    AXUIElementCopyAttributeValue,
    AXUIElementCopyAttributeNames,
    AXUIElementCopyActionNames,
    AXUIElementPerformAction,
    AXUIElementSetAttributeValue,
    AXIsProcessTrusted,
    kAXErrorSuccess,
)
import Quartz

from actra.mac import input_control


# Module-level cache of inspected accessibility elements
# Key: element id (e.g. "@e1") or alias -> Dict containing "element", "pid", "path", "node"
_ELEMENT_CACHE: dict[str, dict[str, Any]] = {}

# Set of roles generally considered interactive / actionable
INTERACTIVE_ROLES = {
    "AXButton",
    "AXTextField",
    "AXTextArea",
    "AXCheckBox",
    "AXRadioButton",
    "AXPopUpButton",
    "AXMenuButton",
    "AXMenuItem",
    "AXLink",
    "AXTab",
    "AXSlider",
    "AXComboBox",
    "AXIncrementor",
    "AXColorWell",
    "AXSearchField",
    "AXStaticText",
    "AXHeading",
    "AXWindow",
    "AXDialog",
    "AXSheet",
    "AXDrawer",
    "AXTable",
    "AXOutline",
    "AXRow",
    "AXCell",
    "AXScrollArea",
}


def check_accessibility_permissions() -> bool:
    """Check if the current process has accessibility permissions."""
    return AXIsProcessTrusted()


def get_frontmost_app_pid() -> int:
    """Get the PID of the frontmost application."""
    workspace = AppKit.NSWorkspace.sharedWorkspace()
    front_app = workspace.frontmostApplication()
    return front_app.processIdentifier() if front_app else -1


def _get_attr(element: Any, attr: str) -> Any:
    """Safely read a single AX attribute."""
    try:
        err, value = AXUIElementCopyAttributeValue(element, attr, None)
        if err == kAXErrorSuccess:
            return value
    except Exception:
        pass
    return None


def _get_actions(element: Any) -> list[str]:
    """Safely read available AX actions for an element."""
    try:
        err, actions = AXUIElementCopyActionNames(element, None)
        if err == kAXErrorSuccess and actions:
            return [str(a) for a in actions]
    except Exception:
        pass
    return []


def _element_to_dict(
    element: Any,
    pid: int,
    path: list[int],
    depth: int,
    max_depth: int,
    id_counter: list[int],
    full_tree: bool = False,
) -> dict[str, Any] | None:
    """Recursively convert an AX element into a plain dict with assigned IDs and caching."""
    node: dict[str, Any] = {}

    # Assign sequential element ID
    id_counter[0] += 1
    elem_id = f"@e{id_counter[0]}"
    node["id"] = elem_id

    role = _get_attr(element, "AXRole")
    node["role"] = str(role) if role else "unknown"

    title = _get_attr(element, "AXTitle")
    if title:
        node["title"] = str(title)

    value = _get_attr(element, "AXValue")
    if value is not None:
        node["value"] = str(value)

    description = _get_attr(element, "AXDescription")
    if description:
        node["description"] = str(description)

    role_description = _get_attr(element, "AXRoleDescription")
    if role_description and full_tree:
        node["role_description"] = str(role_description)

    enabled = _get_attr(element, "AXEnabled")
    if enabled is not None:
        if full_tree or not enabled:  # Only report when disabled or in full mode
            node["enabled"] = bool(enabled)

    focused = _get_attr(element, "AXFocused")
    if focused is not None:
        if full_tree or focused:  # Only report when focused or in full mode
            node["focused"] = bool(focused)

    # Position and size
    pos = _get_attr(element, "AXPosition")
    if pos is not None:
        try:
            node["position"] = {"x": round(float(pos.x), 1), "y": round(float(pos.y), 1)}
        except AttributeError:
            pass

    size = _get_attr(element, "AXSize")
    if size is not None:
        try:
            node["size"] = {"width": round(float(size.width), 1), "height": round(float(size.height), 1)}
        except AttributeError:
            pass

    actions = _get_actions(element)
    if actions:
        node["actions"] = actions

    # Register in in-memory element cache
    _ELEMENT_CACHE[elem_id] = {
        "element": element,
        "pid": pid,
        "path": list(path),
        "node": node,
    }

    # Children traversal
    if depth < max_depth:
        children_ref = _get_attr(element, "AXChildren")
        if children_ref:
            kids: list[dict[str, Any]] = []
            try:
                for idx, child in enumerate(children_ref):
                    child_dict = _element_to_dict(
                        child,
                        pid=pid,
                        path=path + [idx],
                        depth=depth + 1,
                        max_depth=max_depth,
                        id_counter=id_counter,
                        full_tree=full_tree,
                    )
                    if child_dict is not None:
                        kids.append(child_dict)
            except (TypeError, StopIteration):
                pass
            if kids:
                node["children"] = kids

    # Pruning filter if not full_tree
    if not full_tree and depth > 0:
        is_interactive = (
            node["role"] in INTERACTIVE_ROLES
            or bool(actions)
            or bool(node.get("title"))
            or bool(node.get("value"))
            or bool(node.get("description"))
        )
        children = node.get("children", [])
        if not is_interactive and not children:
            return None

        # If it's a pure unlabelled layout wrapper with a single child, collapse it
        if not is_interactive and len(children) == 1 and node["role"] in ("AXGroup", "AXSplitGroup", "AXGenericElement", "AXScrollArea"):
            return children[0]

    return node



def inspect_app(
    pid: int | None = None,
    max_depth: int = 4,
    full_tree: bool = False,
) -> dict[str, Any]:
    """Inspect the accessibility tree of an application.

    Returns a nested dict with assigned element IDs (@e1, @e2...), role, title, value, position, size, children.
    If *pid* is None, inspects the frontmost app.
    """
    global _ELEMENT_CACHE
    if pid is None:
        pid = get_frontmost_app_pid()

    if pid == -1:
        return {"error": "No application found."}

    if not check_accessibility_permissions():
        return {"error": "Accessibility permission not granted. Enable it in System Settings → Privacy & Security → Accessibility."}

    _ELEMENT_CACHE.clear()
    app_element = AXUIElementCreateApplication(pid)
    id_counter = [0]
    tree = _element_to_dict(
        app_element,
        pid=pid,
        path=[],
        depth=0,
        max_depth=max_depth,
        id_counter=id_counter,
        full_tree=full_tree,
    )
    return tree or {"error": "Failed to inspect application accessibility tree."}


def resolve_element(
    element_ref: str,
    pid: int | None = None,
) -> tuple[Any, dict[str, Any]] | None:
    """Resolve an element reference to its AXUIElement and node metadata.

    element_ref can be:
    - An explicit ID: "@e3", "e3", or "3"
    - A role/title descriptor: "button:Search", "Search", "role=AXButton,title=Save"
    """
    if not element_ref:
        return None

    ref_str = str(element_ref).strip()

    # 1. Check ID lookup in cache
    normalized_id = ref_str if ref_str.startswith("@") else f"@{ref_str}"
    if normalized_id in _ELEMENT_CACHE:
        cached = _ELEMENT_CACHE[normalized_id]
        return cached["element"], cached["node"]

    if ref_str.isdigit() and f"@e{ref_str}" in _ELEMENT_CACHE:
        cached = _ELEMENT_CACHE[f"@e{ref_str}"]
        return cached["element"], cached["node"]

    # 2. Check role/title match in cache
    role_filter: str | None = None
    title_filter: str | None = None

    if ":" in ref_str:
        parts = ref_str.split(":", 1)
        role_filter = parts[0].strip().lower()
        title_filter = parts[1].strip().lower()
    else:
        title_filter = ref_str.lower()

    for item in _ELEMENT_CACHE.values():
        node = item["node"]
        n_role = node.get("role", "").lower()
        n_title = (node.get("title") or "").lower()
        n_desc = (node.get("description") or "").lower()
        n_val = str(node.get("value") or "").lower()

        role_matches = (
            role_filter is None
            or role_filter in n_role
            or (role_filter == "button" and "button" in n_role)
            or (role_filter in ("field", "input", "textfield") and "text" in n_role)
        )

        title_matches = (
            title_filter is None
            or title_filter in n_title
            or title_filter in n_desc
            or title_filter in n_val
        )

        if role_matches and title_matches and (n_title or n_desc or n_val):
            return item["element"], node

    # 3. If cache was empty or not matched, perform fresh inspection
    if not _ELEMENT_CACHE:
        inspect_app(pid=pid)
        return resolve_element(element_ref, pid=pid)

    return None


def click_element(
    element_ref: str,
    action: str = "AXPress",
    pid: int | None = None,
) -> bool:
    """Semantically click a UI element via Accessibility API (fallback to element center coordinates)."""
    resolved = resolve_element(element_ref, pid=pid)
    if not resolved:
        return False

    element, node = resolved

    # Try primary action
    err = AXUIElementPerformAction(element, action)
    if err == kAXErrorSuccess:
        return True

    # Try alternative actions
    for alt_action in ("AXPress", "AXConfirm", "AXShowMenu", "AXOpen", "AXPick"):
        if alt_action != action:
            err = AXUIElementPerformAction(element, alt_action)
            if err == kAXErrorSuccess:
                return True

    # Fallback to center coordinates if coordinates exist
    pos = node.get("position")
    size = node.get("size")
    if pos and size:
        cx = pos["x"] + size.get("width", 0) / 2
        cy = pos["y"] + size.get("height", 0) / 2
        input_control.click(cx, cy)
        return True

    return False


def type_into_element(
    element_ref: str,
    text: str,
    clear_first: bool = False,
    pid: int | None = None,
) -> bool:
    """Semantically focus and type text into a UI element."""
    resolved = resolve_element(element_ref, pid=pid)
    if not resolved:
        return False

    element, node = resolved

    # 1. Attempt to focus the element
    AXUIElementSetAttributeValue(element, "AXFocused", True)

    # 2. Attempt to directly set AXValue if not requiring simulated typing
    if not clear_first:
        err = AXUIElementSetAttributeValue(element, "AXValue", text)
        if err == kAXErrorSuccess:
            return True

    # 3. Fallback: Click element center to gain focus, clear if requested, and type
    pos = node.get("position")
    size = node.get("size")
    if pos and size:
        cx = pos["x"] + size.get("width", 0) / 2
        cy = pos["y"] + size.get("height", 0) / 2
        input_control.click(cx, cy)
    else:
        AXUIElementPerformAction(element, "AXPress")

    if clear_first:
        input_control.hotkey("command", "a")
        input_control.press_key("backspace")

    input_control.type_text(text)
    return True


def find_element(
    pid: int | None = None,
    role: str | None = None,
    title: str | None = None,
    max_depth: int = 5,
) -> dict[str, Any] | None:
    """Find a UI element by role and/or title in the accessibility tree."""
    if pid is None:
        pid = get_frontmost_app_pid()

    if not check_accessibility_permissions():
        return None

    tree = inspect_app(pid, max_depth=max_depth, full_tree=True)
    return _search_tree(tree, role, title)


def _search_tree(node: dict[str, Any], role: str | None, title: str | None) -> dict[str, Any] | None:
    """DFS search for a matching element."""
    role_match = role is None or node.get("role") == role
    title_match = title is None or title.lower() in (node.get("title", "") or "").lower()

    if role_match and title_match and (role is not None or title is not None):
        return node

    for child in node.get("children", []):
        result = _search_tree(child, role, title)
        if result is not None:
            return result

    return None


def perform_action(pid: int, element_path: list[int], action: str = "AXPress") -> bool:
    """Perform an accessibility action on an element found by tree path indices."""
    if not check_accessibility_permissions():
        return False

    app_element = AXUIElementCreateApplication(pid)
    current = app_element

    for idx in element_path:
        children = _get_attr(current, "AXChildren")
        if not children or idx >= len(children):
            return False
        current = children[idx]

    err = AXUIElementPerformAction(current, action)
    return err == kAXErrorSuccess


inspect_ui = inspect_app
