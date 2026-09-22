# Actra Requirements

## 1. Scope

These requirements apply to the local macOS Actra implementation.

The product is macOS-only.

There is no iQOO, Android, Office Kit, or phone integration in the current product architecture.

---

## 2. Core Agent

### REQ-001: Natural-language input

Accept free-form natural-language instructions through a local interface.

Initial implementation may use a CLI or minimal local UI.

### REQ-002: General conversation

Support ordinary conversational questions without unnecessarily invoking computer tools.

Examples:

```text
"What is a mutex?"
"Explain recursion."
```

### REQ-003: Intent classification

Distinguish between:

- conversation
- information requests
- local computer tasks
- web research
- tasks requiring clarification
- sensitive operations requiring confirmation

### REQ-004: Planning

Multi-step requests must produce an actionable plan.

### REQ-005: Tool calling

The reasoning model must interact with Actra through structured tools.

### REQ-006: Observation

The agent must be able to inspect current computer/application state between actions.

### REQ-007: Verification

Material outcomes must be verified with concrete evidence.

### REQ-008: Replanning

Failures/unexpected states should allow bounded replanning.

### REQ-009: Bounded execution

Prevent infinite action/retry loops.

---

## 3. Hermes Agent Runtime

### REQ-020: Hermes evaluation

Evaluate the current Hermes Agent implementation before building a duplicate orchestration layer.

Determine:

- model-provider interface
- tool interface
- computer-use capabilities
- planning/execution loop
- context handling
- retry behavior
- skill/plugin mechanisms
- permission/safety behavior
- local model support
- macOS support

### REQ-021: Hermes integration

Where Hermes provides a reliable capability, integrate/reuse it instead of rebuilding the same subsystem.

### REQ-022: Actra control boundary

Actra must retain control over:

- product-level tools
- safety/policy
- final verification
- application-specific behavior
- user-facing behavior

If Hermes conflicts with an Actra requirement, Actra's documented requirement wins and the conflicting Hermes component must be isolated/replaced.

### REQ-023: No accidental dependency lock-in

Core Actra abstractions must not depend on undocumented Hermes internals.

If an adapter is needed, isolate it under a dedicated integration module.

---

## 4. Computer Control

Required capabilities:

```text
open_application()
close_application()
activate_application()
list_running_applications()

take_screenshot()
get_active_application()
get_window_state()
inspect_ui()

click()
double_click()
type_text()
press_key()
hotkey()
scroll()
```

These are conceptual capabilities. Hermes may provide some directly. Do not duplicate them unnecessarily.

---

## 5. macOS Native Control

Use:

- macOS Accessibility
- AppleScript
- Apple Events
- native macOS APIs
- process APIs
- filesystem APIs
- ScreenCaptureKit
- native input mechanisms

Control hierarchy:

```text
deterministic/native API
        ↓
Apple Events / AppleScript
        ↓
Accessibility
        ↓
ScreenCaptureKit + vision
        ↓
keyboard/mouse fallback
```

The exact method can differ by application.

---

## 6. Accessibility

Normalize macOS Accessibility information into an agent-friendly representation.

Where available, expose:

- application
- window
- role
- label/title
- value
- enabled state
- selected state
- available actions
- parent/child relationships

Do not pass raw native objects directly into model prompts.

---

## 7. ScreenCaptureKit

Support screen/window/application observation.

Use visual observation only when necessary.

Prefer targeted application/window capture when available.

Avoid capturing and sending the entire screen after every action.

---

## 8. Keyboard/Mouse

Support keyboard and pointer actions as actuators.

Do not make raw coordinate automation the default architecture.

Semantic element targeting is preferable.

Coordinates can be used when:

- Accessibility is unavailable
- the target is genuinely pixel-based
- vision fallback has identified an element

---

## 9. Filesystem

Support:

```text
find_file()
list_directory()
create_folder()
create_file()
open_file()
copy_file()
move_file()
read_file()
write_file()
```

Basic file management should normally bypass Finder.

Deletion is sensitive/dangerous and requires confirmation.

---

## 10. Browser/Web

Support:

```text
search_web()
open_url()
read_page()
click_element()
type_into_field()
scroll_page()
go_back()
```

When the user requests current information, perform actual web retrieval.

Do not answer freshness-sensitive questions only from static model knowledge.

Use browser APIs, Accessibility, AppleScript, browser automation, or visual interaction as appropriate.

---

## 11. Spreadsheet

Support structured spreadsheet operations.

Canonical task:

> "Add this invoice to my expense tracker."

Expected workflow:

```text
find workbook
→ inspect workbook
→ identify sheet/table
→ map fields
→ append/update row
→ save
→ read back
→ verify
```

Prefer structured workbook editing over visual cell clicking.

---

## 12. Application Skills

Eventually support:

```text
Slack
WhatsApp
Apple Mail
Outlook
Gmail
Microsoft Word
Microsoft Excel
Microsoft PowerPoint
Microsoft Teams
Apple Notes
Spotify
Safari / browsers
general macOS applications
```

Use generic capabilities wherever possible.

Add an application-specific adapter only when it materially improves reliability or capability.

---

## 13. Safety

Every tool has a risk level.

### Safe

- read
- search
- open
- screenshot
- create folder

### Sensitive

- send email
- send message
- overwrite data
- modify externally visible content

### Dangerous

- delete data
- destructive system operation
- purchase
- financial operation
- irreversible action

The model must not bypass policy.

Sensitive/dangerous operations require explicit confirmation unless a future trusted-policy system is explicitly introduced.

---

## 14. Cancellation

Allow active task cancellation.

After cancellation, no new action should start for that task.

Target state:

```text
CANCELLED
```

---

## 15. Execution Logging

Record:

- task ID
- timestamps
- goal
- plan
- tool
- arguments
- result
- observation
- verification
- retry count
- final state

Redact secrets.

---

## 16. Local AI

Primary model:

**Gemma 4 12B**

Run locally on Apple Silicon.

Preferred starting runtime:

```text
Ollama / appropriate Apple-Silicon local runtime
```

The model provider must be abstracted.

The model should support:

- reasoning
- tool/function calling
- general conversation
- multimodal inputs when used

---

## 17. Future Voice

Activation:

```text
ACTRA
```

Architecture:

```text
microphone
→ lightweight wake-word detector
→ speaker verification
→ local ASR
→ Actra/Hermes + Gemma
→ local TTS
```

Use dedicated models/components for wake word, speaker verification, ASR and TTS.

Gemma is not the continuous wake-word detector.

Voice identity filtering is not cryptographic authentication.

Desired TTS characteristics:

- natural pacing
- selectable voice
- accent
- expressive/emotional delivery

---

## 18. Hardware Constraints

```text
MacBook Air M4
16 GB unified memory
256 GB storage
```

Memory is shared across macOS, applications, IDE, Gemma and future specialist models.

Requirements:

- bounded context
- limited screenshot retention
- avoid multiple large models resident unnecessarily
- load specialist models on demand
- monitor memory during multimodal workflows

---

## 19. Cost Constraints

Normal Actra operation should not require paid AI APIs.

Cloud APIs may be used optionally for testing/comparison but are not part of the intended dependency.

---

## 20. Development Constraints

The project is developed using **Antigravity 2.10.0**.

For substantial work, use **3-9 parallel development subagents** when tasks can be safely decomposed.

Useful roles:

- repository analysis
- Gemma/local inference
- Hermes integration
- macOS Accessibility
- AppleScript/Apple Events
- ScreenCaptureKit
- input/filesystem
- application skills
- testing
- security

Rules:

1. Give every subagent a concrete scope.
2. Avoid simultaneous uncoordinated changes to the same files.
3. Ask for explicit findings and test results.
4. The primary agent reconciles results.
5. The primary agent owns final architecture decisions.
6. Run integration tests after merging parallel work.
7. Do not create subagents solely to satisfy a number.

Development subagents are not runtime Actra agents.

---

## 21. Initial Milestones

1. Run Gemma 4 12B locally.
2. Verify Hermes/Gemma compatibility.
3. Verify Hermes computer-use capabilities on macOS.
4. Define Actra integration boundaries.
5. Establish tool registry and safety boundary.
6. Prove direct macOS control independent of the LLM.
7. Connect model → agent runtime → tools.
8. Complete Safari search.
9. Complete filesystem tasks.
10. Complete spreadsheet workflow.
11. Complete web research.
12. Add application skills.
13. Add voice stack.
