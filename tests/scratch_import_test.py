import sys
print(f"Python: {sys.version}")

results = []

def test_import(name, import_stmt):
    try:
        exec(import_stmt)
        results.append((name, 'OK'))
    except Exception as e:
        results.append((name, f'FAIL: {e}'))

test_import('pydantic', 'import pydantic; print(f"  pydantic {pydantic.__version__}")')
test_import('google-genai', 'import google.genai')
test_import('pyobjc-Cocoa', 'import AppKit')
test_import('pyobjc-Quartz', 'import Quartz')
test_import('pyobjc-AppServices', 'from ApplicationServices import AXIsProcessTrusted')
test_import('openpyxl', 'import openpyxl; print(f"  openpyxl {openpyxl.__version__}")')
test_import('Pillow', 'from PIL import Image; print(f"  Pillow {Image.__version__}")')
test_import('dotenv', 'import dotenv')
test_import('pytest', 'import pytest; print(f"  pytest {pytest.__version__}")')

# Test Actra own imports
test_import('actra.models', 'from actra.models import Task, TaskStatus, ToolResult, SafetyLevel')
test_import('actra.llm.base', 'from actra.llm.base import LLMProvider, Message, ToolCall')
test_import('actra.tools.registry', 'from actra.tools.registry import ToolRegistry, tool')
test_import('actra.config', 'from actra.config import Settings')
test_import('actra.mac.permissions', 'from actra.mac.permissions import check_all_permissions')
test_import('actra.logging', 'from actra.logging import ExecutionLogger')

print('\n=== Results ===')
for name, status in results:
    icon = '✅' if status == 'OK' else '❌'
    print(f'{icon} {name}: {status}')
