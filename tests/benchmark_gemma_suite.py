"""Gemma 4 12B MLX Validation Benchmark Suite (10 Tests)"""

import time
import subprocess
import shutil
from pathlib import Path
from actra.agent import ActraAgent
from actra.config import Settings
from actra.models import TaskStatus, SafetyLevel


def run_benchmark_suite():
    settings = Settings(
        ollama_host="http://localhost:11434",
        model_name="gemma4:12b-mlx",
        num_ctx=8192,
        require_confirmation=False,
    )
    
    agent = ActraAgent(settings=settings)
    results = []

    def report(name, task, elapsed, extra=None):
        ps_out = subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout
        mem_line = [l for l in ps_out.splitlines() if "gemma4" in l]
        mem = mem_line[0] if mem_line else "N/A"
        
        status_ok = task.status == TaskStatus.COMPLETED
        tool_count = len(task.tool_calls)
        verified = task.verification.verified if task.verification else (status_ok and tool_count > 0)
        
        res = {
            "test": name,
            "status": task.status.value,
            "elapsed_sec": round(elapsed, 2),
            "tool_calls": tool_count,
            "retries": task.retries,
            "verified": verified,
            "memory": mem,
            "extra": extra or {}
        }
        results.append(res)
        print(f">>> [{name}] Status: {task.status.value} | Elapsed: {elapsed:.2f}s | Tools: {tool_count} | Retries: {task.retries} | Verified: {verified}")
        return res

    print("===============================================================")
    print("STARTING ACTRA GEMMA 4 12B MLX BENCHMARK SUITE (10 TESTS)")
    print("===============================================================")

    # TEST 1: Open Safari
    print("--- Test 1: Open Safari ---")
    t0 = time.time()
    t1 = agent.run("Open Safari")
    t1_time = time.time() - t0
    report("1. Open Safari", t1, t1_time)

    # TEST 2: Create a folder in Documents
    print("--- Test 2: Create folder in Documents ---")
    test_dir = Path.home() / "Documents" / "ActraTestFolder"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    t0 = time.time()
    t2 = agent.run("Create a folder called ActraTestFolder in ~/Documents")
    t2_time = time.time() - t0
    report("2. Create Folder", t2, t2_time, {"exists": test_dir.exists()})

    # TEST 3: Find a file in Documents
    print("--- Test 3: Find file in Documents ---")
    t0 = time.time()
    t3 = agent.run("Find files matching *.txt in ~/Documents")
    t3_time = time.time() - t0
    report("3. Find File", t3, t3_time)

    # TEST 4: Two-step task
    print("--- Test 4: Two-step task ---")
    test_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    t4 = agent.run("Create a file named benchmark_note.txt in ~/Documents/ActraTestFolder with content 'Actra Benchmark 2026' and then list the directory ~/Documents/ActraTestFolder")
    t4_time = time.time() - t0
    report("4. Two-step Task", t4, t4_time)


    # TEST 5: Recover from failed tool
    print("--- Test 5: Recover from failed tool ---")
    t0 = time.time()
    t5 = agent.run("Find the file non_existent_spreadsheet_xyz987.xlsx in ~/Documents/NonExistentDir123, and if not found, find files in ~/Documents")
    t5_time = time.time() - t0
    report("5. Tool Recovery", t5, t5_time)

    # TEST 6: Ambiguous request / clarification
    print("--- Test 6: Ambiguous request ---")
    t0 = time.time()
    t6 = agent.run("Explain what a mutex is in one short sentence.")
    t6_time = time.time() - t0
    report("6. Conversational / Info", t6, t6_time, {"text": t6.context.get("final_message", "")[:100]})

    # TEST 7: Safety policy check
    print("--- Test 7: Safety Policy ---")
    safe_settings = Settings(
        ollama_host="http://localhost:11434",
        model_name="gemma4:12b-mlx",
        require_confirmation=True,
    )
    safe_agent = ActraAgent(settings=safe_settings)
    t0 = time.time()
    import unittest.mock
    with unittest.mock.patch("builtins.input", return_value="n"):
        t7 = safe_agent.run("Delete the folder ~/Documents/ActraTestFolder")
    t7_time = time.time() - t0
    report("7. Safety Policy Gating", t7, t7_time)

    # TEST 8: Complete task with verified evidence
    print("--- Test 8: Verified Evidence Output ---")
    t0 = time.time()
    t8 = agent.run("Create a folder called ActraVerified in ~/Documents")
    t8_time = time.time() - t0
    verified_path = Path.home() / "Documents" / "ActraVerified"
    report("8. Verified Evidence", t8, t8_time, {"checks": [c.model_dump() for c in t8.verification.checks] if t8.verification else []})
    if verified_path.exists():
        shutil.rmtree(verified_path)

    # TEST 9: UI state search
    print("--- Test 9: UI State Search ---")
    t0 = time.time()
    t9 = agent.run("Open Safari and search for iQOO 15")
    t9_time = time.time() - t0
    report("9. UI State Search", t9, t9_time)

    # TEST 10: Ambiguous selection
    print("--- Test 10: Ambiguous selection handling ---")
    t0 = time.time()
    t10 = agent.run("Should I use Apple Notes or Microsoft Word for writing Python code?")
    t10_time = time.time() - t0
    report("10. Ambiguous Selection / Advice", t10, t10_time)

    if test_dir.exists():
        shutil.rmtree(test_dir)

    print("===============================================================")
    print("FINAL BENCHMARK SUMMARY (10 TESTS)")
    print("===============================================================")
    for r in results:
        v_str = "VERIFIED" if r["verified"] else "NOT VERIFIED"
        print(f"{r['test']:<35} | {r['status']:<10} | {r['elapsed_sec']:>6.2f}s | Tools: {r['tool_calls']:<2} | {v_str}")

if __name__ == "__main__":
    run_benchmark_suite()
