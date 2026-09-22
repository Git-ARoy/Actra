# Actra Project Overview

## 1. Project Identity

**Project name:** Actra  
**Platform:** macOS only  
**Primary development machine:** MacBook Air M4, 16 GB unified memory, 256 GB storage  
**Primary reasoning model:** Gemma 4 12B, running locally  
**Agent runtime:** Hermes Agent, to be evaluated/integrated as the runtime/orchestration foundation  
**Development environment:** Antigravity 2.10.0 with 3-9 parallel development subagents when useful

Actra is a local-first AI productivity and computer-use agent for macOS.

The core idea is simple:

> The user describes the desired outcome. Actra reasons about the task, selects appropriate tools, operates the Mac, observes what happened, verifies the result, and either completes the task or replans/asks for clarification.

Core loop:

```text
USER INTENT
    ↓
UNDERSTAND
    ↓
PLAN
    ↓
SELECT TOOL
    ↓
EXECUTE
    ↓
OBSERVE
    ↓
VERIFY
    ↓
COMPLETE
    │
    └── unexpected state/failure → REPLAN / ASK USER
```

Actra is not intended to be merely a chatbot, a macro recorder, or a remote-desktop application.

---

## 2. Problem

Modern productivity is fragmented across:

- desktop applications
- browser tabs
- files and folders
- spreadsheets
- documents
- email
- collaboration tools
- messaging applications
- notes
- media applications
- information on the web
- physical documents and handwritten information

Users often know what result they want but must manually convert that intent into a sequence of application-specific operations.

Example:

> "Add this invoice to my expense tracker."

Today this can require:

1. inspecting the invoice
2. finding the correct workbook
3. opening the workbook
4. locating the correct worksheet
5. identifying the appropriate columns
6. adding the values
7. adding the current date/time
8. saving
9. checking that the change actually persisted

Actra should reduce this to an outcome-level instruction and execute the workflow.

Another example:

> "Turn this into a project plan."

The larger multimodal product should eventually be able to perceive an image/document/whiteboard, structure the information, and create useful digital artifacts.

Another example:

> "Take these meeting notes and prepare the follow-up."

The agent should infer decisions, action items, people and deadlines, then create the appropriate outputs.

The underlying problem is:

> **the gap between understanding what the user wants and actually completing the work on the computer.**

---

## 3. Target Users

Actra targets people who perform information-heavy computer work:

- students
- software developers
- researchers
- professionals
- founders
- project managers
- administrators
- knowledge workers

The immediate development and validation environment is the developer's own Mac.

---

## 4. Background and Motivation

Actra originated as a Productivity-track idea for an iQOO hackathon.

The concept initially included an iQOO phone acting as a multimodal interface, with camera, microphone and notification awareness, and a future phone-to-computer connection.

The project has deliberately been **decoupled from the hackathon hardware ecosystem**.

Authoritative current scope:

- macOS only
- local-first
- Gemma 4 12B
- Hermes Agent as an evaluated/integrated agent runtime
- native macOS automation
- local voice stack eventually
- no iQOO dependency
- no Android dependency
- no Office Kit integration
- no custom phone-to-Mac WebSocket bridge

The project is now being treated as a standalone Mac AI-agent product rather than an iQOO-specific hackathon prototype.

---

## 5. Core Product Thesis

Actra implements:

> **Intent → Reasoning → Action → Verification**

Users should express outcomes rather than procedures.

Examples:

```text
"Open Safari and search for iQOO 15."
```

```text
"Find my expense tracker in Documents."
```

```text
"Create a folder called Hackathon in Documents."
```

```text
"Add this expense to my tracker."
```

```text
"Search the internet for the latest M4 benchmarks and summarize them."
```

The agent determines the appropriate procedure.

---

## 6. Hermes + Gemma Responsibility Split

Hermes Agent is an **agent-runtime/orchestration foundation**, not the product identity and not the reasoning model.

Gemma 4 12B is the intended **local reasoning model**.

Conceptually:

```text
Actra
  ↓
Hermes Agent Runtime
  ↓
Gemma 4 12B
  ↓
Actra/Hermes tools
  ↓
macOS / Browser / Application capabilities
```

The exact integration must be validated against the installed/current Hermes implementation before relying on any particular Hermes API.

Actra must retain ownership of:

- product behavior
- tool policy
- safety rules
- application skills
- verification requirements
- macOS integration decisions
- user experience
- future voice system

Do not duplicate Hermes functionality if Hermes already supplies it reliably.

Do not blindly delegate safety-critical behavior to Hermes.

---

## 7. High-Level Goals

### Goal A: Fully local reasoning

Run Gemma 4 12B locally on the Mac.

Normal operation should not require a paid cloud LLM API.

### Goal B: General Mac computer use

Support:

- macOS Accessibility
- AppleScript
- Apple Events
- native macOS APIs
- filesystem operations
- application APIs
- ScreenCaptureKit
- keyboard/mouse input
- vision-based interaction as fallback

### Goal C: Agentic execution

Actra must perform multi-step workflows rather than merely explain how to perform them.

### Goal D: Reliable verification

The agent must obtain evidence that the requested outcome was achieved.

### Goal E: Broad productivity

The architecture should eventually support:

- Slack
- WhatsApp
- Apple Mail
- Outlook
- Gmail
- Microsoft Word
- Microsoft Excel
- Microsoft PowerPoint
- Microsoft Teams
- Apple Notes
- Spotify
- browsers
- arbitrary/general macOS applications

### Goal F: Natural interaction

The eventual product should support:

- text input
- voice input
- wake word "ACTRA"
- speaker verification
- natural spoken responses
- expressive voice
- general conversation

These are modular future capabilities.

---

## 8. Non-Goals

Do not add the following without a new explicit requirement:

- iQOO integration
- Android application
- Office Kit
- phone-to-Mac networking
- custom phone WebSocket bridge
- Windows/Linux support
- mandatory cloud inference
- production SaaS
- multi-user accounts
- billing
- arbitrary unrestricted shell access
- multi-agent runtime swarm
- RAG/vector database without a concrete use case
- remote-desktop architecture
- unnecessary microservices
- unnecessary database infrastructure

---

## 9. Product Principles

### Outcome over procedure

The user states the result.

### Agent over chatbot

The system should execute work where tools permit.

### Deterministic over probabilistic

Use APIs/structured operations whenever possible.

### Semantic over coordinates

Use accessibility/UI semantics before raw coordinates.

### Vision as fallback

Use visual reasoning when structured control is inadequate.

### Verify over assume

Never claim completion without evidence.

### Local-first

Keep AI inference and user data local whenever practical.

### Modular specialist models

Do not force Gemma to perform every voice subsystem.
