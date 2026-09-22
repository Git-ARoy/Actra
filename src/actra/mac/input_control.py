import time
from Quartz import (
    CGEventCreateMouseEvent, CGEventPost, CGEventCreateKeyboardEvent,
    CGEventSetFlags, kCGEventMouseMoved, kCGEventLeftMouseDown,
    kCGEventLeftMouseUp, kCGHIDEventTap, kCGEventKeyDown, kCGEventKeyUp,
    kCGEventFlagMaskShift, kCGEventFlagMaskControl,
    kCGEventFlagMaskAlternate, kCGEventFlagMaskCommand,
    CGEventCreateScrollWheelEvent, kCGScrollEventUnitLine,
    CGPoint
)

KEY_CODES: dict[str, int] = {
    'a': 0, 's': 1, 'd': 2, 'f': 3, 'h': 4, 'g': 5, 'z': 6, 'x': 7,
    'c': 8, 'v': 9, 'b': 11, 'q': 12, 'w': 13, 'e': 14, 'r': 15,
    'y': 16, 't': 17, '1': 18, '2': 19, '3': 20, '4': 21, '6': 22,
    '5': 23, '=': 24, '9': 25, '7': 26, '-': 27, '8': 28, '0': 29,
    ']': 30, 'o': 31, 'u': 32, '[': 33, 'i': 34, 'p': 35, 'return': 36,
    'enter': 36, 'l': 37, 'j': 38, "'": 39, 'k': 40, ';': 41, '\\': 42,
    ',': 43, '/': 44, 'n': 45, 'm': 46, '.': 47, 'tab': 48, 'space': 49,
    '`': 50, 'delete': 51, 'escape': 53, 'command': 55, 'shift': 56,
    'capslock': 57, 'option': 58, 'control': 59, 'right_shift': 60,
    'right_option': 61, 'right_control': 62, 'f5': 96, 'f6': 97, 'f7': 98,
    'f3': 99, 'f8': 100, 'f9': 101, 'f11': 103, 'f13': 105, 'f14': 107,
    'f10': 109, 'f12': 111, 'f15': 113, 'home': 115, 'pageup': 116,
    'forward_delete': 117, 'f4': 118, 'end': 119, 'f2': 120, 'pagedown': 121,
    'f1': 122, 'left': 123, 'right': 124, 'down': 125, 'up': 126
}

SHIFT_CHARS = {
    '~': '`', '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6',
    '&': '7', '*': '8', '(': '9', ')': '0', '_': '-', '+': '=', '{': '[',
    '}': ']', '|': '\\', ':': ';', '"': "'", '<': ',', '>': '.', '?': '/'
}

def click(x: float, y: float) -> None:
    """Click at screen coordinates."""
    point = CGPoint(x, y)
    mouse_down = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, point, 0)
    mouse_up = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, point, 0)
    CGEventPost(kCGHIDEventTap, mouse_down)
    time.sleep(0.01)
    CGEventPost(kCGHIDEventTap, mouse_up)

def double_click(x: float, y: float) -> None:
    """Double-click at screen coordinates."""
    click(x, y)
    time.sleep(0.1)
    click(x, y)

def move_mouse(x: float, y: float) -> None:
    """Move mouse to screen coordinates."""
    point = CGPoint(x, y)
    move = CGEventCreateMouseEvent(None, kCGEventMouseMoved, point, 0)
    CGEventPost(kCGHIDEventTap, move)

def _create_key_event(keycode: int, down: bool, flags: int = 0):
    event = CGEventCreateKeyboardEvent(None, keycode, down)
    if flags:
        CGEventSetFlags(event, flags)
    return event

def type_text(text: str, interval: float = 0.02) -> None:
    """Type text string character by character using CGEvents."""
    for char in text:
        shift_needed = char.isupper() or char in SHIFT_CHARS
        base_char = SHIFT_CHARS.get(char, char.lower())
        
        if base_char not in KEY_CODES:
            continue
            
        keycode = KEY_CODES[base_char]
        flags = kCGEventFlagMaskShift if shift_needed else 0
        
        down_event = _create_key_event(keycode, True, flags)
        up_event = _create_key_event(keycode, False, flags)
        
        CGEventPost(kCGHIDEventTap, down_event)
        time.sleep(0.01)
        CGEventPost(kCGHIDEventTap, up_event)
        time.sleep(interval)

def press_key(key: str) -> None:
    """Press and release a single key by name."""
    if key.lower() not in KEY_CODES:
        return
    keycode = KEY_CODES[key.lower()]
    CGEventPost(kCGHIDEventTap, _create_key_event(keycode, True))
    time.sleep(0.01)
    CGEventPost(kCGHIDEventTap, _create_key_event(keycode, False))

def hotkey(*keys: str) -> None:
    """Press a key combination (e.g., hotkey('command', 'l') for Cmd+L)."""
    flags = 0
    key_events = []
    modifiers = {'command': kCGEventFlagMaskCommand, 'shift': kCGEventFlagMaskShift,
                 'option': kCGEventFlagMaskAlternate, 'control': kCGEventFlagMaskControl}
    
    last_key = keys[-1].lower()
    for key in keys[:-1]:
        if key.lower() in modifiers:
            flags |= modifiers[key.lower()]
            
    if last_key in KEY_CODES:
        keycode = KEY_CODES[last_key]
        down_event = _create_key_event(keycode, True, flags)
        up_event = _create_key_event(keycode, False, flags)
        
        CGEventPost(kCGHIDEventTap, down_event)
        time.sleep(0.01)
        CGEventPost(kCGHIDEventTap, up_event)

def scroll(clicks: int, x: float | None = None, y: float | None = None) -> None:
    """Scroll at the current or given position. Positive = up, negative = down."""
    if x is not None and y is not None:
        move_mouse(x, y)
    
    # 1 for lines, clicks for amount (negative = down)
    scroll_event = CGEventCreateScrollWheelEvent(None, kCGScrollEventUnitLine, 1, clicks)
    CGEventPost(kCGHIDEventTap, scroll_event)
