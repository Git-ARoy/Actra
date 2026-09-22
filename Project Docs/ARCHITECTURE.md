# Actra Architecture

## 1. Architecture Objective

Actra is a local macOS AI computer-use agent.

The architecture separates:

- product layer
- agent runtime
- reasoning model
- Actra tools
- macOS control
- application skills
- observation
- verification
- safety

---

## 2. High-Level Architecture

```text
                         USER
                           |
                     text / future voice
                           |
                           v
                 +---------------------+
                 |      ACTRA          |
                 | Product / Policy    |
                 | Context / UX       |
                 +----------+----------+
                            |
                            v
                 +---------------------+
                 |   HERMES AGENT      |
                 | Runtime /           |
                 | orchestration       |
                 +----------+----------+
                            |
                            v
                 +---------------------+
                 |    GEMMA 4 12B      |
                 |    Local Brain      |
                 +----------+----------+
                            |
                      structured calls
                            |
                 +----------+----------+
                 | Actra Tool Registry |
                 +----------+----------+
                            |
         +------------------+------------------+
         |                  |                  |
         v                  v                  v
     Computer          Files/System      Application Skills
       Tools              Tools                  |
         |                  |                    |
         +------------------+--------------------+
                            |
                            v
                 +---------------------+
                 |   macOS Control     |
                 +----------+----------+
                            |
          +-----------------+------------------+
          |                 |                  |
          v                 v                  v
     Accessibility    Apple Events/Script  ScreenCaptureKit
          |                 |                  |
          +-----------------+------------------+
                            |
                            v
                    macOS Applications
```

---

## 3. Responsibility Separation

### Actra

Owns:

- product behavior
- user-facing interaction
- system prompt/product policies
- safety/policy decisions
- application skill selection
- verification requirements
- local model configuration
- future voice layer
- integration adapters

### Hermes

Potentially supplies:

- agent execution loop
- tool orchestration
- planning primitives
- computer-use runtime
- task execution infrastructure
- reusable skills/tool support

Do not duplicate these if the existing Hermes implementation can provide them reliably.

### Gemma 4 12B

Owns:

- intent interpretation
- reasoning
- planning decisions
- function/tool selection
- multimodal interpretation where appropriate
- general conversation
- response generation

### Mac Control Layer

Owns:

- Accessibility
- Apple Events
- AppleScript
- ScreenCaptureKit
- keyboard/mouse
- native application/process interactions
- filesystem access

---

## 4. Hermes Integration Rule

Before implementing a custom agent loop, inspect the installed/current Hermes Agent version.

Determine:

- model backend support
- local model support
- tool schema
- tool lifecycle
- observation model
- execution loop
- retry behavior
- context management
- skill architecture
- computer-use implementation
- macOS support
- safety hooks

Create a narrow Actra↔Hermes adapter when necessary.

Do not make Actra depend on undocumented Hermes internal classes.

---

## 5. LLM Layer

Recommended structure:

```text
src/actra/llm/
├── base.py
├── ollama.py
└── schemas.py
```

Conceptual provider:

```python
class LLMProvider:
    def generate(...): ...
    def generate_with_tools(...): ...
    def generate_multimodal(...): ...
```

The rest of the code must not assume Ollama-specific response formats.

---

## 6. Tool Layer

Recommended:

```text
src/actra/tools/
├── registry.py
├── computer.py
├── filesystem.py
├── browser.py
├── spreadsheet.py
├── system.py
└── safety.py
```

Tool properties:

```text
name
description
input schema
implementation
risk level
side-effect metadata
```

Tools return structured results.

---

## 7. macOS Control Layer

Recommended:

```text
src/actra/macos/
├── accessibility.py
├── screen_capture.py
├── input.py
├── applications.py
├── apple_events.py
└── permissions.py
```

If native Swift code is required, isolate it rather than moving the whole project to Swift.

Potential native Swift component:

```text
native/macos/
└── ActraMacBridge/
```

Use native Swift only where framework-level access materially improves reliability.

---

## 8. Control Hierarchy

The tool implementation should select the most reliable mechanism.

```text
1. deterministic/native API
2. application API
3. Apple Events / AppleScript
4. Accessibility
5. ScreenCaptureKit + vision
6. keyboard/mouse
```

This ordering is conceptual, not absolute. The best control method depends on the application and operation.

Example:

```text
find file
→ filesystem/search API

edit xlsx
→ structured workbook library

scriptable app
→ Apple Events

generic UI button
→ Accessibility

unstructured/canvas UI
→ screenshot + vision + input
```

---

## 9. Observation

Observation should be layered by cost.

### Cheap

```text
active application
window title
filesystem state
process state
```

### Semantic

```text
Accessibility tree
focused element
available actions
```

### Visual

```text
screenshot
```

Do not send expensive screenshots to Gemma when structured state is sufficient.

---

## 10. Verification

Each material task needs expected-state criteria.

Example:

```text
Goal:
Add expense to workbook.

Expected:
new row exists

Checks:
- workbook found
- correct sheet
- row present
- values match
- saved
```

Verifier result:

```json
{
  "verified": true,
  "checks": [
    {
      "name": "row_present",
      "passed": true
    }
  ]
}
```

---

## 11. Application Skills

Suggested:

```text
src/actra/applications/
├── common/
├── slack/
├── whatsapp/
├── apple_mail/
├── outlook/
├── gmail/
├── word/
├── excel/
├── powerpoint/
├── teams/
├── notes/
└── spotify/
```

Skills should reuse common Actra tools.

An application adapter may choose:

- API
- Apple Events
- filesystem
- Accessibility
- browser automation
- visual interaction

based on reliability.

---

## 12. Browser

Browser is treated as an environment/tool.

```text
Gemma
  ↓
browser tool
  ↓
search/open/read/action
  ↓
observation
  ↓
Gemma
```

Current-information requests must perform actual retrieval.

---

## 13. Spreadsheet

Spreadsheet flow:

```text
Goal
 ↓
Locate workbook
 ↓
Inspect structure
 ↓
Map fields
 ↓
Structured edit
 ↓
Save
 ↓
Read back
 ↓
Verify
```

Visual spreadsheet manipulation is a fallback.

---

## 14. Safety Flow

```text
Gemma proposes action
        ↓
Actra/Hermes tool layer
        ↓
Policy Manager
        ↓
Risk check
   +----+----+
   |         |
 safe     sensitive/dangerous
   |         |
 execute   confirmation
```

The model must not bypass the policy layer.

---

## 15. Future Voice Architecture

```text
Microphone
   ↓
VAD
   ↓
Wake-word detector: ACTRA
   ↓
Speaker verification
   ↓
Local ASR
   ↓
Actra/Hermes
   ↓
Gemma 4 12B
   ↓
Local TTS
```

Specialist components:

- wake-word detector
- speaker-embedding model
- ASR
- TTS

Do not keep all large specialist models loaded simultaneously on a 16 GB machine without justification.

---

## 16. Runtime Deployment

Local:

```text
macOS
├── Actra product/runtime
├── Hermes Agent
├── Gemma local model runtime
├── macOS control layer
└── application skills
```

No mandatory cloud server.

---

## 17. Suggested Repository Structure

```text
actra/
├── README.md
├── PROJECT_OVERVIEW.md
├── REQUIREMENTS.md
├── ARCHITECTURE.md
├── API_SPEC.md
├── TECH_DECISIONS.md
├── pyproject.toml
├── .gitignore
├── .env.example
│
├── src/
│   └── actra/
│       ├── main.py
│       │
│       ├── agent/
│       │   ├── integration.py
│       │   ├── context.py
│       │   ├── policy.py
│       │   └── verifier.py
│       │
│       ├── hermes/
│       │   ├── adapter.py
│       │   ├── config.py
│       │   └── compatibility.py
│       │
│       ├── llm/
│       │   ├── base.py
│       │   ├── ollama.py
│       │   └── schemas.py
│       │
│       ├── tools/
│       │   ├── registry.py
│       │   ├── computer.py
│       │   ├── filesystem.py
│       │   ├── browser.py
│       │   ├── spreadsheet.py
│       │   └── system.py
│       │
│       ├── macos/
│       │   ├── accessibility.py
│       │   ├── screen_capture.py
│       │   ├── input.py
│       │   ├── applications.py
│       │   ├── apple_events.py
│       │   └── permissions.py
│       │
│       ├── applications/
│       │   ├── common/
│       │   ├── slack/
│       │   ├── whatsapp/
│       │   ├── apple_mail/
│       │   ├── outlook/
│       │   ├── gmail/
│       │   ├── word/
│       │   ├── excel/
│       │   ├── powerpoint/
│       │   ├── teams/
│       │   ├── notes/
│       │   └── spotify/
│       │
│       ├── models/
│       │   ├── task.py
│       │   ├── tool.py
│       │   └── execution.py
│       │
│       └── logging/
│           └── execution_log.py
│
├── native/
│   └── macos/
│       └── ActraMacBridge/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── manual/
│
└── scripts/
```

Do not create all modules immediately. Add them as requirements become active.

---

## 18. Development Workflow

Use Antigravity 2.10.0.

For substantial independent work, use 3-9 parallel development subagents.

Example:

```text
A: Repository / dependency audit
B: Gemma + Ollama
C: Hermes integration
D: Accessibility
E: Apple Events
F: ScreenCaptureKit/input
G: filesystem/spreadsheet/browser
H: testing
I: safety review
```

The primary agent integrates their work and owns the final codebase.

---

## 19. Resource Constraints

The Mac has 16 GB unified memory.

Track:

- Gemma memory
- context size
- screenshot memory
- auxiliary model memory
- application/IDE memory

Prefer on-demand loading of specialist models.
