"""ActraAgent — the main orchestrator implementing the full agent loop.

    receive goal → plan → execute → observe → verify → complete / replan
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any

import httpx

from actra.config import Settings
from actra.logging import ExecutionLogger
from actra.llm.base import LLMProvider, LLMResponse
from actra.llm.ollama_provider import OllamaProvider
from actra.models import Task, TaskStatus, ToolResult, TaskEvent


from actra.agent.context import ContextManager
from actra.agent.executor import Executor
from actra.agent.memory import MemoryStore, set_default_store
from actra.agent.planner import Planner
from actra.agent.state import transition, is_terminal
from actra.agent.verifier import Verifier
from actra.hud import get_hud_server
from actra.tools.registry import ToolRegistry
from actra.tools.safety import SafetyGate

# Ensure all tool modules are imported so @tool decorators run
import actra.tools.filesystem  # noqa: F401
import actra.tools.applications  # noqa: F401
import actra.tools.computer  # noqa: F401
import actra.tools.observation  # noqa: F401
import actra.tools.browser  # noqa: F401
import actra.tools.spreadsheet  # noqa: F401
import actra.tools.fusion  # noqa: F401


class ActraAgent:
    """Top-level agent that receives a goal and drives it to completion.

    Implements the core loop:
        PLAN → EXECUTE → OBSERVE → VERIFY → (COMPLETE | REPLAN)

    Exposes the internal task API:
        submit_task, get_task_status, cancel_task, get_task_result
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings.load()
        self._logger = ExecutionLogger(
            log_dir=self._settings.log_dir,
            level=self._settings.log_level,
        )

        # LLM provider
        self._llm: LLMProvider = self._create_llm_provider()

        # Tool system
        self._registry = ToolRegistry()
        self._registry.register_all_defaults()
        self._safety = SafetyGate(
            confirmation_mode=self._settings.no_confirm
        )

        # Native HUD server & confirmation delegation
        self._hud = get_hud_server()
        try:
            self._hud.start()
            self._hud.set_user_command_handler(self._handle_hud_user_command)
            self._safety.set_prompt_delegate(
                lambda tool, args, lvl: self._hud.request_confirmation_sync(tool, args, lvl)
            )
            self._start_heartbeat()
        except Exception as e:
            self._logger.warning("HUD server initialization warning: %s", e)

        # Agent components
        self._planner = Planner(self._llm, self._registry)
        self._executor = Executor(self._registry, self._safety, self._logger)
        self._verifier = Verifier()

        # Memory store
        self._memory = MemoryStore(self._settings.memory_db_path)
        set_default_store(self._memory)

        # Active tasks
        self._tasks: dict[str, Task] = {}

    # ------------------------------------------------------------------
    # Internal task API (transport-agnostic)
    # ------------------------------------------------------------------

    def submit_task(self, goal: str, context: dict[str, Any] | None = None) -> Task:
        """Accept a new goal and return a Task with RECEIVED status."""
        task = Task(goal=goal, context=context or {})
        self._tasks[task.task_id] = task
        self._logger.info("📋 New task: %s [%s]", goal, task.task_id[:8])
        self._logger.trace(
            task_id=task.task_id,
            event="task_received",
            extra={"goal": goal},
        )
        self._hud.broadcast_task_update(task, step_description="Task received")
        return task

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """Return the current status of a task."""
        task = self._tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "step_index": task.step_index,
            "retries": task.retries,
        }

    def cancel_task(self, task_id: str) -> dict[str, Any]:
        """Cancel an active task."""
        task = self._tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        if is_terminal(task.status):
            return {"task_id": task_id, "status": task.status.value, "message": "Already terminal"}
        transition(task, TaskStatus.CANCELLED)
        self._memory.log_task_outcome(task)
        self._hud.broadcast_task_update(task, step_description="Task cancelled")
        self._logger.info("🚫 Task cancelled [%s]", task_id[:8])
        return {"task_id": task_id, "status": "CANCELLED"}

    def get_task_result(self, task_id: str) -> dict[str, Any]:
        """Return the final result of a completed task."""
        task = self._tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        result: dict[str, Any] = {
            "task_id": task.task_id,
            "status": task.status.value,
            "goal": task.goal,
        }
        if task.status == TaskStatus.COMPLETED:
            result["message"] = "Task completed successfully."
        elif task.status == TaskStatus.FAILED:
            result["error"] = {"code": "TASK_FAILED", "message": task.error_message or "Unknown failure"}
        return result

    # ------------------------------------------------------------------
    # Main execution loop
    # ------------------------------------------------------------------

    def run(self, goal: str, context: dict[str, Any] | None = None) -> Task:
        """Submit and execute a task synchronously, returning the completed Task."""
        task = self.submit_task(goal, context)
        self._execute_loop(task)
        return task

    def _execute_loop(self, task: Task) -> None:
        """Drive the task through the agent loop until terminal state."""
        ctx = ContextManager()
        ctx.add_user_goal(task.goal)

        # Maximum total iterations to prevent runaway loops
        max_iterations = 25

        for iteration in range(max_iterations):
            if is_terminal(task.status):
                break

            # --- PLAN ---
            transition(task, TaskStatus.PLANNING)
            self._logger.step(task.task_id, f"Planning (iteration {iteration + 1})...")
            self._hud.broadcast_task_update(task, step_description=f"Planning (iteration {iteration + 1})")

            try:
                response = self._planner.next_action(ctx)
            except Exception as e:
                self._logger.error("Planner error: %s", str(e))
                task.error_message = f"Planner error: {e}"
                transition(task, TaskStatus.FAILED)
                self._hud.broadcast_task_update(task, step_description=f"Planner error: {e}")
                break

            # --- TEXT RESPONSE (completion or clarification) ---
            if not response.tool_calls:
                text = response.text or ""
                self._logger.info("💬 Agent: %s", text)
                ctx.add_assistant(text=text, raw=response.raw)
                self._logger.trace(
                    task_id=task.task_id,
                    event="agent_response",
                    extra={"text": text},
                )

                # If tool calls were executed, run Level 2 Goal Verification
                if task.tool_calls:
                    transition(task, TaskStatus.VERIFYING)
                    self._hud.broadcast_task_update(task, step_description="Verifying goal outcome")
                    goal_result = self._verifier.verify_goal(task)
                    task.verification = goal_result
                    self._logger.trace(
                        task_id=task.task_id,
                        event="goal_verification",
                        verification="PASSED" if goal_result.verified else "FAILED",
                        extra={
                            "checks": [c.model_dump() for c in goal_result.checks],
                            "reason": goal_result.reason,
                        },
                    )
                    if not goal_result.verified:
                        task.retries += 1
                        self._logger.warning(
                            "⚠️ Goal verification failed (retry %d/%d): %s",
                            task.retries, task.max_retries, goal_result.reason
                        )
                        if task.retries >= task.max_retries:
                            task.error_message = f"Goal verification failed: {goal_result.reason}"
                            transition(task, TaskStatus.FAILED)
                            self._hud.broadcast_task_update(task, step_description="Goal verification failed")
                            break
                        ctx.add_observation(f"Goal verification check failed: {goal_result.reason}")
                        continue

                transition(task, TaskStatus.COMPLETED)
                task.context["final_message"] = text
                self._hud.broadcast_task_update(task, step_description=text or "Completed")
                break


            # --- EXECUTE TOOL CALLS ---
            # Record the assistant's tool calls turn once in context
            ctx.add_assistant(tool_calls=response.tool_calls, raw=response.raw)

            for tool_call in response.tool_calls:
                if is_terminal(task.status):
                    break

                tool_name = tool_call.name
                arguments = tool_call.arguments

                transition(task, TaskStatus.EXECUTING)
                self._logger.step(task.task_id, f"Executing: {tool_name}({arguments})")
                self._hud.broadcast_task_update(task, step_description=f"Executing {tool_name}")

                # Execute
                result = self._executor.execute(task.task_id, tool_name, arguments)

                # Record in task and context
                task.tool_calls.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result.model_dump(),
                })
                task.step_index += 1
                ctx.add_tool_result(tool_name, result)

                # --- OBSERVE ---
                transition(task, TaskStatus.OBSERVING)
                self._hud.broadcast_task_update(task, step_description=f"Observing {tool_name}")

                # --- VERIFY ---
                transition(task, TaskStatus.VERIFYING)
                self._hud.broadcast_task_update(task, step_description=f"Verifying {tool_name}")
                verified = self._verifier.verify(tool_name, result)
                reason = self._verifier.reason(tool_name, result)
                self._logger.trace(
                    task_id=task.task_id,
                    event="verification",
                    tool=tool_name,
                    verification="PASSED" if verified else "FAILED",
                    extra={"reason": reason},
                )

                if not verified:
                    task.retries += 1
                    self._logger.warning(
                        "⚠️ Verification failed for %s (retry %d/%d): %s",
                        tool_name, task.retries, task.max_retries, reason,
                    )
                    if task.retries >= task.max_retries:
                        task.error_message = f"Max retries reached. Last failure: {reason}"
                        transition(task, TaskStatus.FAILED)
                        self._hud.broadcast_task_update(task, step_description=f"Failed: {reason}")
                        break
                    # Re-plan on next iteration
                    ctx.add_observation(f"Verification failed: {reason}")

        else:
            # Loop exhausted without reaching terminal state
            if not is_terminal(task.status):
                task.error_message = "Maximum iterations reached without completion."
                transition(task, TaskStatus.FAILED)

        # Final log
        self._logger.info(
            "🏁 Task %s → %s", task.task_id[:8], task.status.value,
        )
        self._logger.trace(
            task_id=task.task_id,
            event=f"task_{task.status.value.lower()}",
            extra={"final_message": task.context.get("final_message", "")},
        )
        self._memory.log_task_outcome(task)
        self._hud.broadcast_task_update(task, step_description=task.context.get("final_message", task.status.value))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _create_llm_provider(self) -> LLMProvider:
        """Instantiate the local Ollama LLM provider."""
        return OllamaProvider(
            model_name=self._settings.model_name,
            host=self._settings.ollama_host,
            num_ctx=self._settings.num_ctx,
        )

    def _check_llm_health(self) -> bool:
        """Ping local Ollama instance to verify LLM availability."""
        try:
            url = f"{self._settings.ollama_host.rstrip('/')}/api/tags"
            with httpx.Client(timeout=2.0) as client:
                res = client.get(url)
                return res.status_code == 200
        except Exception:
            return False

    def _handle_hud_user_command(self, action: str, payload: dict[str, Any]) -> None:
        """Execute or dispatch commands received from the Native HUD."""
        if action == "submit_goal":
            goal = payload.get("goal", "").strip()
            if goal:
                self._logger.info("📩 Goal received from HUD: %s", goal)
                # Run the task in background daemon thread
                threading.Thread(
                    target=self.run,
                    args=(goal,),
                    daemon=True,
                    name=f"HUDTask_{goal[:12]}"
                ).start()
        elif action == "cancel_task":
            task_id = payload.get("task_id")
            if task_id:
                self.cancel_task(task_id)

    def _start_heartbeat(self) -> None:
        """Start a periodic health broadcast thread to keep the HUD updated."""
        def _heartbeat_loop():
            while True:
                try:
                    llm_ok = self._check_llm_health()
                    active_tasks = sum(1 for t in self._tasks.values() if not is_terminal(t.status))
                    self._hud.broadcast_health(
                        llm_status="connected" if llm_ok else "offline",
                        cpu_percent=0.0,
                        memory_percent=0.0,
                        active_tasks=active_tasks,
                    )
                except Exception:
                    pass
                time.sleep(3.0)

        threading.Thread(target=_heartbeat_loop, daemon=True, name="ActraHUDHeartbeat").start()

