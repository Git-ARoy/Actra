# Actra API Specification

## 1. Scope

Phrase 1 is a local macOS product.

No public cloud API is required.

The interfaces below are internal contracts designed to isolate Actra from the Hermes runtime and the LLM provider.

---

## 2. Internal Task Interface

### submit_task

```python
submit_task(goal: str, context: dict | None = None) -> Task
```

Request:

```json
{
  "goal": "Open Safari and search for iQOO 15",
  "context": {
    "source": "local_cli"
  }
}
```

Response:

```json
{
  "task_id": "uuid",
  "status": "RECEIVED",
  "goal": "Open Safari and search for iQOO 15"
}
```

---

## 3. Task Status

```text
RECEIVED
PLANNING
EXECUTING
OBSERVING
VERIFYING
WAITING_FOR_CONFIRMATION
COMPLETED
FAILED
CANCELLED
```

---

## 4. get_task_status

```python
get_task_status(task_id: str) -> TaskStatus
```

Example:

```json
{
  "task_id": "uuid",
  "status": "EXECUTING",
  "current_step": "Typing query into Safari",
  "retry_count": 0
}
```

---

## 5. cancel_task

```python
cancel_task(task_id: str) -> TaskStatus
```

After cancellation, no new tool calls should be initiated.

---

## 6. get_task_result

```python
get_task_result(task_id: str) -> TaskResult
```

Success:

```json
{
  "task_id": "uuid",
  "status": "COMPLETED",
  "message": "Safari was opened and the search was completed.",
  "evidence": []
}
```

Failure:

```json
{
  "task_id": "uuid",
  "status": "FAILED",
  "error": {
    "code": "VERIFICATION_FAILED",
    "message": "The requested state could not be confirmed."
  }
}
```

---

## 7. Tool Contract

Conceptual interface:

```python
class Tool:
    name: str
    description: str
    input_schema: dict
    risk_level: str

    def execute(self, arguments: dict) -> ToolResult:
        ...
```

Tool result:

```json
{
  "success": true,
  "tool": "open_application",
  "data": {
    "application": "Safari"
  },
  "error": null
}
```

Failure:

```json
{
  "success": false,
  "tool": "find_file",
  "data": null,
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "No suitable file was found."
  }
}
```

The actual tool-dispatch mechanism may be supplied by Hermes. Actra should normalize it behind its own internal interface.

---

## 8. LLM Provider Contract

```python
class LLMProvider:
    def generate(self, messages, **kwargs):
        ...

    def generate_with_tools(self, messages, tools, **kwargs):
        ...

    def generate_multimodal(self, messages, inputs, **kwargs):
        ...
```

Primary provider:

```text
Local Gemma 4 12B
```

Initial runtime candidate:

```text
Ollama
```

Do not spread Ollama-specific response structures throughout Actra.

---

## 9. Hermes Adapter Contract

Actra should isolate Hermes integration.

Conceptual:

```python
class HermesAdapter:
    def submit(self, task) -> Task:
        ...

    def execute(self, task_id) -> TaskResult:
        ...

    def cancel(self, task_id) -> None:
        ...
```

This is intentionally an abstract contract, not a claim about Hermes' exact public API.

Before implementing the adapter, inspect the installed/current Hermes version.

---

## 10. Internal Events

Suggested:

```text
task_received
planning_started
plan_created
tool_started
tool_completed
observation_created
verification_started
verification_passed
verification_failed
confirmation_required
task_completed
task_failed
task_cancelled
```

Example:

```json
{
  "task_id": "uuid",
  "event": "tool_completed",
  "timestamp": "2026-08-23T00:00:00Z",
  "data": {
    "tool": "open_application",
    "success": true
  }
}
```

---

## 11. Authentication

No authentication is needed for the local single-user runtime.

Do not add OAuth/JWT/accounts without a new requirement.

---

## 12. Secrets

Normal operation should not require cloud API keys.

Optional provider keys must:

- stay in environment variables/local secret storage
- never be committed
- be redacted from logs

---

## 13. Future Voice Boundary

Voice should eventually call the same task interface.

```text
voice
  ↓
STT
  ↓
submit_task()
```

The task engine should not care whether the input came from text or speech.

---

## 14. Future Client Boundary

Do not define a phone network API.

Actra is macOS-only.

No Office Kit integration.

No custom phone WebSocket integration.

The current task API exists for internal separation of concerns, testing and future local interfaces.
