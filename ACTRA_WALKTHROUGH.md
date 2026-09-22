# Actra: Comprehensive Walkthrough, Architecture, and Capabilities Guide

**Actra** is a local-first AI productivity and computer-use agent built specifically for macOS. It bridges the gap between high-level user goals and low-level desktop execution—understanding intent, formulating execution plans, interacting directly with macOS native APIs and applications, observing system state, and verifying outcomes with deterministic evidence.

---

## 1. Executive Summary & Core Identity

### 1.1 What is Actra?
Unlike passive chatbots or brittle macro recorders, Actra is an **autonomous computer-use agent**. Given an outcome-oriented instruction, Actra interacts directly with the operating system through a multi-tier control hierarchy (Apple Events, Accessibility trees, native filesystem/document APIs, and Quartz input events) to accomplish the task autonomously.

```
┌────────────────────────────────────────────────────────────────────────┐
│                              USER INTENT                               │
│              "Open Safari and search for latest benchmarks"            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                              UNDERSTAND                                │
│                   Parse goal and extract constraints                   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                                 PLAN                                   │
│              Reason about required tools & execution steps             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                             SELECT TOOL                                │
│              Map step to deterministic API or GUI interaction          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                               EXECUTE                                  │
│              Run action via macOS Control / Tool Registry              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                               OBSERVE                                  │
│             Capture UI hierarchy, window info, or screenshots          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                                VERIFY                                  │
│             Level 1: Tool execution | Level 2: Goal outcome            │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
             [Check Passed]                   [Check Failed]
                    │                                │
                    ▼                                ▼
┌──────────────────────────────────────┐ ┌───────────────────────────────┐
│               COMPLETE               │ │         REPLAN / RETRY        │
│          Deliver final summary       │ │   Feed error back to planner  │
└──────────────────────────────────────┘ └───────────────────────────────┘
```

### 1.2 Core Architectural Principles
* **Outcome over Procedure:** Users declare *what* they want done; the agent determines *how*.
* **Local-First & Privacy-Centric:** Designed to run with local reasoning models (such as Gemma 4 12B via Ollama) on Apple Silicon without mandatory cloud API dependencies.
* **Deterministic over Probabilistic:** Prefers structured APIs, AppleScript/Apple Events, and file handles over imprecise coordinate clicking whenever possible.
* **Semantic over Coordinate-based:** Uses macOS Accessibility (AXUIElement) trees to find UI elements semantically rather than guessing pixel coordinates.
* **Vision as Fallback:** Uses ScreenCaptureKit and visual reasoning when semantic accessibility trees or APIs are unavailable (e.g. custom canvas UIs).
* **Verify over Assume:** Never claims success without inspecting live OS state (process lists, URL bars, file existence, spreadsheet contents).

---

## 2. System Architecture

Actra's codebase is structured into modular layers, separating agent reasoning from operating system mechanics.

```
actra/
├── src/actra/
│   ├── agent/                 # Core Agent Engine
│   │   ├── agent.py           # ActraAgent orchestrator & Task API
│   │   ├── planner.py         # Prompt engineering & tool calling logic
│   │   ├── executor.py        # Safe tool invocation & logging
│   │   ├── verifier.py        # Two-level verification engine
│   │   ├── context.py         # Multi-turn conversational memory & history
│   │   └── state.py           # Task lifecycle state machine
│   ├── llm/                   # LLM Provider Abstraction
│   │   ├── base.py            # Base provider interface & standard schemas
│   │   └── ollama_provider.py # Local Ollama provider (Gemma 4 12B)
│   ├── mac/                   # Native macOS Control Layer
│   │   ├── accessibility.py   # PyObjC ApplicationServices (AXUIElement)
│   │   ├── apple_events.py    # AppleScript execution & NSWorkspace events
│   │   ├── input_control.py   # Quartz CGEvent mouse & keyboard emulation
│   │   ├── screen_capture.py  # macOS screencapture & Window management
│   │   ├── cua_bridge.py      # Unified Computer-Use Bridge (MCP / Native)
│   │   └── permissions.py     # Accessibility & Screen Recording validation
│   ├── tools/                 # Tool Registry & Domain Implementations
│   │   ├── registry.py        # Tool registration decorators & schema generation
│   │   ├── safety.py          # Policy manager & confirmation gates
│   │   ├── applications.py    # App management (open, activate, quit, list)
│   │   ├── browser.py         # Safari automation & web navigation
│   │   ├── filesystem.py      # File & folder I/O operations
│   │   ├── spreadsheet.py     # Excel (.xlsx) data manipulation via openpyxl
│   │   ├── computer.py        # Raw mouse clicks, typing, hotkeys, scrolling
│   │   └── observation.py     # Screenshot capture & AX tree inspection
│   ├── models/                # Pydantic data contracts (Task, ToolResult, etc.)
│   ├── config/                # Environment configuration & settings
│   ├── logging/               # Structured execution tracer & logger
│   └── main.py                # CLI entry point & REPL interface
```

### 2.1 State Machine Lifecycle
Every task progresses through formal states:
1. `RECEIVED`: Task initialized with user goal.
2. `PLANNING`: The LLM reasons about the goal and context, choosing next actions.
3. `EXECUTING`: The Executor calls the selected tool with safety checks.
4. `OBSERVING`: Tool results and environmental observations are gathered.
5. `VERIFYING`: Verifier runs Level 1 (Action) and Level 2 (Goal) checks.
6. `WAITING_FOR_CONFIRMATION`: Triggered if a `DANGEROUS` or `SENSITIVE` action requires user approval.
7. `COMPLETED` / `FAILED` / `CANCELLED`: Terminal states.

---

## 3. Comprehensive Tool Catalog & Capabilities

Actra provides 22+ built-in tools across 6 core functional domains:

### 3.1 Browser Automation (Safari)
Automates web browsing using native Apple Events and AppleScript for high reliability.

| Tool | Parameters | Safety Level | Description |
| :--- | :--- | :--- | :--- |
| `safari_open` | None | `SAFE` | Opens or activates the Safari browser. |
| `safari_navigate` | `url` (string) | `SAFE` | Navigates Safari to a specified URL. |
| `safari_search` | `query` (string) | `SAFE` | Performs a Google search in Safari. |
| `safari_get_url` | None | `SAFE` | Retrieves the URL of the active Safari tab. |
| `safari_get_title` | None | `SAFE` | Retrieves the title of the frontmost Safari window. |

### 3.2 macOS Application Management
Controls application lifecycles and window focus via `NSWorkspace` and AppleScript.

| Tool | Parameters | Safety Level | Description |
| :--- | :--- | :--- | :--- |
| `open_application` | `name` (string) | `SAFE` | Opens or activates an application by name. |
| `activate_application` | `name` (string) | `SAFE` | Brings an existing application window to front. |
| `close_application` | `name` (string) | `SENSITIVE` | Quits a running application. |
| `list_running_applications` | None | `SAFE` | Returns a list of active application names. |
| `get_active_application` | None | `SAFE` | Identifies the currently focused application. |

### 3.3 Filesystem & Documents
Provides structured file manipulation without needing arbitrary shell execution.

| Tool | Parameters | Safety Level | Description |
| :--- | :--- | :--- | :--- |
| `find_file` | `directory` (str), `pattern` (str) | `SAFE` | Recursively searches for files matching glob patterns. |
| `list_directory` | `path` (string) | `SAFE` | Lists folder contents with metadata (type, size). |
| `create_folder` | `path` (string) | `SAFE` | Creates directories recursively (`mkdir -p`). |
| `create_file` | `path` (str), `content` (str) | `SENSITIVE` | Creates a new file with specified content. |
| `read_file` | `path` (str), `max_chars` (int) | `SAFE` | Reads UTF-8 file content with safe truncation. |
| `write_file` | `path` (str), `content` (str) | `SENSITIVE` | Overwrites or updates an existing file. |
| `move_file` | `source` (str), `destination` (str) | `SENSITIVE` | Moves or renames files/folders. |
| `copy_file` | `source` (str), `destination` (str) | `SAFE` | Copies files or directories. |
| `open_file` | `path` (string) | `SAFE` | Opens a file using default macOS associations (`open`). |
| `delete_file` | `path` (string) | `DANGEROUS` | Deletes a file or directory permanently. |

### 3.4 Structured Data & Spreadsheets (Excel)
Edits `.xlsx` workbooks directly using `openpyxl` without needing GUI interaction.

| Tool | Parameters | Safety Level | Description |
| :--- | :--- | :--- | :--- |
| `open_workbook` | `path` (string) | `SAFE` | Inspects workbook sheet names and dimensions. |
| `inspect_workbook` | `path` (str), `sheet` (str) | `SAFE` | Reads sheet column headers, row counts, and bounds. |
| `append_table_row` | `path` (str), `sheet` (str), `values` (dict) | `SENSITIVE` | Maps dictionary keys to column headers and appends a row. |
| `save_workbook` | `path` (string) | `SAFE` | Persists workbook modifications to disk. |
| `read_last_row` | `path` (str), `sheet` (str) | `SAFE` | Reads the most recent row for verification. |

### 3.5 GUI & Computer-Use Input (Quartz Events)
Low-level fallback input controls using macOS `CGEvent` and PyObjC.

| Tool | Parameters | Safety Level | Description |
| :--- | :--- | :--- | :--- |
| `click` | `x` (float), `y` (float) | `SENSITIVE` | Performs a mouse left-click at coordinate. |
| `double_click` | `x` (float), `y` (float) | `SENSITIVE` | Performs a mouse double-click at coordinate. |
| `type_text` | `text` (string) | `SENSITIVE` | Types keystrokes into the active element. |
| `press_key` | `key` (string) | `SAFE` | Presses a single key (e.g. `return`, `tab`, `escape`). |
| `hotkey` | `keys` (string) | `SAFE` | Triggers key combinations (e.g. `command+space`). |
| `scroll` | `amount` (int), `x` (float), `y` (float) | `SAFE` | Scrolls mouse wheel up/down. |

### 3.6 Observation & Inspection
Gathers context about active windows and visual states.

| Tool | Parameters | Safety Level | Description |
| :--- | :--- | :--- | :--- |
| `take_screenshot` | None | `SAFE` | Captures display image, saves to disk, returns base64. |
| `get_window_info` | None | `SAFE` | Retrieves window bounds, title, and owning process. |
| `inspect_ui` | `max_depth` (int) | `SAFE` | Dumps the active window's Accessibility tree. |

---

## 4. Two-Level Verification & Self-Correction Engine

A distinguishing feature of Actra is that it **never assumes an action succeeded simply because the LLM generated a tool call**.

```
                           TOOL EXECUTION RESULT
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │   Level 1: Action Verifier    │
                     │  Did the tool execute cleanly?│
                     └───────────────┬───────────────┘
                                     │
                             [Passed / Failed]
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │    Level 2: Goal Verifier     │
                     │ Does OS state match the goal? │
                     └───────────────┬───────────────┘
                                     │
                         ┌───────────┴───────────┐
                         ▼                       ▼
                    [VERIFIED]              [NOT VERIFIED]
                         │                       │
                         ▼                       ▼
                  Task Completed         Feed Error Back to Context
                                         & Trigger Planner Re-plan
```

### 4.1 Level 1: Action Verification
Checks whether the immediate tool invocation returned valid data and produced its intended side-effect:
* `create_folder`: Verifies that the path actually exists on the filesystem and is a directory.
* `safari_search`: Verifies that a valid search URL or query was generated and dispatched.
* `append_table_row`: Verifies that `row_number > 0` was written to the spreadsheet.

### 4.2 Level 2: Goal Verification
Before the agent finishes, the Verifier queries macOS subsystems to obtain empirical evidence:
* **Browser Tasks:** Verifies `Safari` is actively running in the process table, queries AppleScript for the front document's active URL, and verifies search query keywords appear in the document title or URL.
* **File Operations:** Checks disk storage to verify that created/written files exist and contain non-zero bytes.
* **Spreadsheet Tasks:** Reads back the last row from the file to ensure the written fields match what was requested.

### 4.3 Autonomous Re-planning
If verification fails and `retries < max_retries`:
1. The failure reason (e.g. `"Verification failed: Target path not verified on disk"`) is injected as a system observation into conversational context.
2. The agent transitions to `PLANNING` and dynamically attempts an alternative approach.
3. If errors persist beyond `max_retries` (default 3), the task gracefully marks as `FAILED` with detailed diagnostics.

---

## 5. Safety, Policy, and Permission System

Actra classifies every operation into a safety tier to protect user data:

```
                  ┌───────────────────────────────────┐
                  │          PROPOSED ACTION          │
                  └─────────────────┬─────────────────┘
                                    │
                                    ▼
                  ┌───────────────────────────────────┐
                  │         Safety Gate Policy        │
                  └─────────────────┬─────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
   [ SAFE TIER ]            [ SENSITIVE TIER ]        [ DANGEROUS TIER ]
   • find_file              • create_file             • delete_file
   • read_file              • write_file              • arbitrary wipe
   • safari_search          • append_table_row
   • inspect_ui             • type_text / click
          │                         │                         │
          ▼                         ▼                         ▼
   Auto-Executed             Auto-Executed or         Prompts User for
                             Interactive Prompt       Explicit Confirmation
```

* **Interactive Confirmation:** Destructive operations like `delete_file` require explicit user consent via standard CLI prompt `[y/N]`.
* **Automation Override:** The `--no-confirm` flag allows power users to bypass confirmation for trusted script execution.
* **macOS Permissions:** Actra validates required system permissions on startup:
  1. **Accessibility (`AXUIElement`)**: For inspecting UI elements and sending Quartz events.
  2. **Screen Recording (`CGDisplayStream`)**: For taking screenshots.
  3. **Apple Events (`Automation`)**: For controlling Safari, Finder, and system apps.

---

## 6. Detailed Walkthrough & Usage Examples

### 6.1 Installation and Setup
```bash
# 1. Clone repository
cd Actra

# 2. Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install in editable mode with dependencies
pip install -e ".[dev]"

# 4. Configure environment
cp .env.example .env

# 5. Ensure Ollama is running with Gemma 4
ollama run gemma4:12b
```

---

### 6.2 Example Walkthrough 1: Web Research & Browser Navigation

**Command:**
```bash
actra "Open Safari and search for iQOO 15"
```

**Step-by-Step Agent Execution Flow:**
1. **Goal Ingestion:** Goal is parsed into Task with status `RECEIVED`.
2. **Planning Iteration 1:**
   - Planner detects browser intent and selects `safari_search(query="iQOO 15")`.
3. **Execution:**
   - Safety check passes (`SAFE` tier).
   - AppleScript activates Safari and opens `https://www.google.com/search?q=iQOO+15`.
4. **Observation & Action Verification:**
   - Tool returns success. Level 1 Verifier checks that URL encoding and invocation succeeded.
5. **Planning Iteration 2:**
   - Planner checks context and concludes goal is satisfied. Emits completion text.
6. **Goal Verification (Level 2):**
   - Verifier checks process list (`Safari` running).
   - Verifier checks active document URL (`https://www.google.com/search?q=iQOO+15`).
   - All evidence checks pass (`safari_process_active`, `safari_url_loaded`, `safari_search_query_present`).
7. **Completion:** Status changes to `COMPLETED`.

---

### 6.3 Example Walkthrough 2: File System Organization & Note Creation

**Command:**
```bash
actra "Create a folder named ProjectPlan in ~/Documents and write a summary file inside it"
```

**Step-by-Step Agent Execution Flow:**
1. **Planning Step 1:** Planner calls `create_folder(path="~/Documents/ProjectPlan")`.
2. **Execution & Level 1 Verification:**
   - Folder is created on disk.
   - Verifier checks `Path("~/Documents/ProjectPlan").exists() == True`.
3. **Planning Step 2:** Planner calls `create_file(path="~/Documents/ProjectPlan/summary.md", content="# Project Plan\n\nGoals and deliverables...")`.
4. **Execution & Level 1 Verification:**
   - File is written. Verifier checks that bytes were written and file exists.
5. **Goal Verification (Level 2):**
   - Verifier runs `create_file_verified_on_disk` and `create_folder_verified_on_disk`.
6. **Completion:** Agent prints confirmation: `"Created directory ~/Documents/ProjectPlan and wrote summary.md."`

---

### 6.4 Example Walkthrough 3: Spreadsheet Manipulation

**Command:**
```bash
actra "Add an expense of $45 for Lunch on 2026-09-14 to ~/Documents/expenses.xlsx"
```

**Step-by-Step Agent Execution Flow:**
1. **Inspection:** Planner calls `inspect_workbook(path="~/Documents/expenses.xlsx")`.
2. **Observation:** Tool returns header columns: `["Date", "Category", "Amount", "Description"]`.
3. **Appended Row:** Planner calls `append_table_row(path="~/Documents/expenses.xlsx", values={"Date": "2026-09-14", "Category": "Food", "Amount": 45, "Description": "Lunch"})`.
4. **Level 1 Verification:** Verifier checks row index increased.
5. **Level 2 Verification:** `read_last_row` confirms matched fields in the spreadsheet.
6. **Completion:** Agent finishes task cleanly.

---

### 6.5 Interactive REPL Mode
```bash
actra --interactive
```
```text
╔══════════════════════════════════════════════╗
║   Actra — macOS Computer-Use AI Agent        ║
║   Phase 1: Laptop-only Prototype             ║
╚══════════════════════════════════════════════╝

Interactive mode. Type your goal, or 'quit' to exit.

🎯 Goal: Find all pdf files in Downloads
Executing: find_file({'directory': '~/Downloads', 'pattern': '*.pdf'})
💬 Agent: Found 4 PDF files in Downloads: report.pdf, receipt.pdf, slides.pdf, invoice.pdf
✨ Status: COMPLETED | Steps: 1

🎯 Goal:
```

---

## 7. Extensibility & Future Roadmap

* **Voice Stack (Future Phase):** Local VAD (Voice Activity Detection), custom wake-word engine (`"ACTRA"`), speaker verification, and local fast TTS/ASR.
* **Expanded Application Adapters:** Deep integrations for Slack, Apple Mail, Microsoft Teams, Apple Notes, Spotify, and Microsoft Office.
* **Visual Fallback Pipeline:** Combining ScreenCaptureKit with localized object detection and OCR for canvas-based apps (Figma, Miro, legacy games) lacking AX trees.
* **Hermes Agent Runtime Integration:** Evaluating Hermes Agent as an orchestration runtime while retaining Actra's macOS control and verification layers.
