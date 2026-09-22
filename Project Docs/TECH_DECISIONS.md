# Actra Technical Decisions

## TD-001: macOS-only

**Decision:** Actra targets macOS only.

**Reason:** The available development machine is a MacBook Air M4 and macOS provides first-class Accessibility, Apple Events, AppleScript and ScreenCaptureKit capabilities.

**Rejected:** Windows/Linux/cross-platform support from the beginning.

---

## TD-002: Gemma 4 12B is the primary local reasoning model

**Decision:** Use Gemma 4 12B locally.

**Reason:** Actra requires reasoning, function/tool calling, multimodal understanding, planning and general conversation. The project explicitly prioritizes local inference.

**Rejected:** Downgrading to a smaller model purely for memory convenience.

The 16 GB machine is a constraint, but the selected product target is Gemma 4 12B.

---

## TD-003: Local inference over mandatory cloud APIs

**Decision:** Run Gemma locally through an appropriate local runtime, initially evaluating Ollama.

**Reason:**

- no recurring API cost
- no small external request limits
- improved data locality
- offline operation
- predictable development

**Rejected:** Cloud-only Gemini/OpenAI architecture.

Optional cloud APIs can be used for comparison, never as a mandatory dependency.

---

## TD-004: Hermes Agent as runtime foundation

**Decision:** Evaluate and integrate the current Hermes Agent implementation as the agent-runtime/orchestration foundation where it provides reliable capabilities.

Hermes is not the product and does not replace Gemma.

Target separation:

```text
Actra
  ↓
Hermes Runtime
  ↓
Gemma 4 12B
  ↓
Actra/Hermes tools
  ↓
macOS
```

**Reason:** Hermes can potentially provide substantial agent/computer-use infrastructure that would otherwise need to be rebuilt.

**Rejected:** Automatically writing a completely custom planner/executor runtime before inspecting Hermes.

---

## TD-005: Hermes must not own Actra's safety boundary

**Decision:** Actra retains final control over safety/policy and verification.

**Reason:** Third-party/runtime capabilities should not silently determine what high-impact actions the product is allowed to execute.

**Rejected:** Blindly trusting a runtime's default permissions.

---

## TD-006: Do not duplicate Hermes capabilities

**Decision:** If Hermes already reliably implements a required capability, integrate/reuse it.

**Reason:** Duplicate agent loops, tool systems and computer-use mechanisms create complexity and inconsistent behavior.

**Rejected:** Reimplementing all Hermes functions inside `agent.py`.

---

## TD-007: Isolate Hermes integration

**Decision:** Use an Actra adapter around Hermes.

**Reason:** Hermes can change, and Actra should not spread Hermes-specific internals through the entire codebase.

**Rejected:** Importing Hermes implementation internals from every module.

---

## TD-008: Python as primary language

**Decision:** Python is the primary language for Actra.

**Reason:** AI/LLM integration, orchestration, filesystem, spreadsheet, browser and automation ecosystems are strong.

**Rejected:** Swift-only architecture.

---

## TD-009: Swift only for native Mac needs

**Decision:** Use Swift selectively for native macOS components.

Potential areas:

- Accessibility
- ScreenCaptureKit
- native Apple Event integration
- permission handling
- native input

**Rejected:** Rewriting the entire project in Swift.

---

## TD-010: Layered macOS control

**Decision:**

```text
deterministic/native API
→ application API
→ Apple Events / AppleScript
→ Accessibility
→ ScreenCaptureKit + vision
→ keyboard/mouse
```

**Reason:** Different applications expose different control surfaces.

---

## TD-011: No PyAutoGUI-only design

**Decision:** Keyboard/mouse automation is a low-level actuator/fallback.

**Reason:** Fixed coordinates and visual-only macros are fragile.

**Rejected:** Screenshot → coordinate click as the universal model.

---

## TD-012: Structured tools, not arbitrary generated code

**Decision:** Gemma should interact through typed tools.

**Reason:**

- validation
- safety
- logging
- testing
- predictable side effects
- provider independence

**Rejected:** Unrestricted generated Python or shell commands as the default actuator.

---

## TD-013: No unrestricted shell tool

**Decision:** Do not expose unrestricted `run_shell(command)` as the default tool.

**Reason:** It provides excessive privilege and makes safety/verification difficult.

A restricted shell capability can be added only for a clearly justified use case.

---

## TD-014: Observation and verification are mandatory

**Decision:** Material workflows use:

```text
act → observe → verify → continue/replan
```

**Reason:** Action success does not equal outcome success.

**Rejected:** One-shot action sequences without validation.

---

## TD-015: Structured spreadsheet manipulation

**Decision:** Prefer spreadsheet libraries/APIs for workbook operations.

**Reason:** Deterministic, testable and easier to verify.

**Rejected:** Visual cell clicking as the primary spreadsheet architecture.

---

## TD-016: No database initially

**Decision:** Use in-memory state and optionally JSON/SQLite.

**Reason:** Single-user local application.

**Rejected:** PostgreSQL/MongoDB.

---

## TD-017: No RAG/vector DB initially

**Decision:** Do not add retrieval infrastructure without a demonstrated product requirement.

**Reason:** The primary challenge is computer execution.

**Rejected:** RAG as generic agent boilerplate.

---

## TD-018: No multi-agent runtime swarm

**Decision:** Actra runtime should use the Hermes-supported agent model rather than a swarm of autonomous runtime agents.

**Reason:** Multiple runtime agents add coordination complexity without a current requirement.

**Rejected:** Planner/researcher/browser/filesystem/UI agents as permanent autonomous peers.

Important distinction:

**Antigravity 3-9 parallel subagents are development workers, not Actra runtime agents.**

---

## TD-019: Generic tools + application skills

**Decision:** Build reusable capabilities and add targeted application skills.

**Reason:** Slack, WhatsApp, Mail, Outlook, Gmail, Office apps, Teams, Notes and Spotify have different APIs/control surfaces, but share common concepts.

**Rejected:** Separate incompatible automation frameworks for every application.

---

## TD-020: Browser is an agent tool

**Decision:** Internet research should use real browser/web retrieval when requested.

**Reason:** Current facts should be retrieved rather than guessed from static model weights.

**Rejected:** Treating the local model's knowledge as a live internet connection.

---

## TD-021: Voice uses specialist models

**Decision:** Future voice uses separate local components for:

- wake word
- speaker verification
- ASR
- TTS

**Reason:** These workloads have different latency and model-size requirements.

**Rejected:** Making Gemma the continuous voice-processing stack.

---

## TD-022: Wake word is separate from speaker verification

**Decision:** Use:

```text
wake word
→ speaker verification
→ ASR
```

**Reason:** Detecting "ACTRA" does not establish who said it.

---

## TD-023: No continuous Gemma wake-word inference

**Decision:** Never continuously run Gemma on raw microphone audio just to detect "ACTRA".

**Reason:** Wasteful in compute and memory.

Use a lightweight detector.

---

## TD-024: Local expressive TTS

**Decision:** Voice output should be local-first and eventually support natural pacing, accents and expressiveness.

**Reason:** Consistent with the local product architecture.

Emotional/expressive quality is secondary to reliable task execution.

---

## TD-025: No polished UI before core agent works

**Decision:** Begin with CLI/minimal UI.

**Reason:** The high-risk work is computer use and verification.

---

## TD-026: Local deployment

**Decision:** Run Actra locally on the Mac.

**Reason:** The agent needs direct access to applications, files and UI.

**Rejected:** Cloud-hosted execution as the primary architecture.

---

## TD-027: Actra is not remote desktop

**Decision:** Actra is an AI computer-use agent, not an AnyDesk/VNC replacement.

**Reason:** The user states an outcome and the agent performs the workflow.

Remote display/control may be used for debugging but is not the product architecture.

---

## TD-028: No iQOO / Office Kit integration

**Decision:** The final product architecture is macOS-only.

Explicitly excluded:

- iQOO
- Android
- Office Kit
- phone-to-Mac WebSocket
- phone bridge

**Reason:** The product has been decoupled from the original hackathon-specific device concept.

This decision supersedes earlier discussions that considered Office Kit or a phone-based control architecture.

---

## TD-029: Phrase 1 is laptop-local

**Decision:** The current implementation must be usable entirely from the Mac.

**Reason:** This establishes and validates the computer-use foundation independently.

---

## TD-030: Memory-aware AI

**Decision:** Treat 16 GB unified memory as a hard practical constraint.

Rules:

- bound context
- avoid retaining unnecessary screenshots
- load specialist models on demand
- do not keep several large models resident without justification

---

## TD-031: Model evaluation is task-based

**Decision:** Evaluate Gemma/Hermes using real Actra workflows.

Measure:

- tool selection accuracy
- argument correctness
- task completion
- recovery behavior
- latency
- memory
- unnecessary actions
- verification accuracy

**Reason:** Generic LLM benchmarks do not prove computer-use reliability.

---

## TD-032: First milestone before feature expansion

**Decision:** The first complete workflow is:

> "Open Safari and search for iQOO 15."

Success requires:

```text
understand
→ plan
→ tool call
→ macOS action
→ observe
→ verify
→ report
```

Only after this is reliable should the team expand into spreadsheets, browser research, application skills and voice.

---

## TD-033: Antigravity parallel development

**Decision:** Use 3-9 parallel subagents for substantial decomposable development work in Antigravity 2.10.0.

Suggested workstreams:

```text
repository/dependency audit
Gemma/Ollama
Hermes integration
Accessibility
AppleScript/Apple Events
ScreenCaptureKit
input/filesystem
application skills
testing
security
```

The subagents do not define Actra's runtime architecture.

The primary agent integrates their work and makes final decisions.
