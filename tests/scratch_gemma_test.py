import json
import httpx

OLLAMA_URL = "http://localhost:11434/api/chat"

tools = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Open a macOS application by name",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Application name"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "safari_search",
            "description": "Search for a query in Safari browser",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Take a screenshot of the current screen",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

messages = [
    {"role": "system", "content": "You are Actra, a macOS computer-use AI agent. Use the provided tools to accomplish tasks. Always use tools - do not just describe what to do."},
    {"role": "user", "content": "Open Safari and search for iQOO 15"}
]

print("=== Test 1: Tool calling ===")
resp = httpx.post(OLLAMA_URL, json={
    "model": "gemma4:12b-mlx",
    "messages": messages,
    "tools": tools,
    "stream": False
}, timeout=120.0)
result = resp.json()
print(json.dumps(result, indent=2))

if result.get("message", {}).get("tool_calls"):
    print("\n✅ Tool calls generated successfully")
    for tc in result["message"]["tool_calls"]:
        print(f"  Tool: {tc['function']['name']}")
        print(f"  Args: {tc['function']['arguments']}")
else:
    print("\n❌ No tool calls generated")
    print(f"Response text: {result.get('message', {}).get('content', 'N/A')}")

# Test 2: Multi-turn with tool result
print("\n=== Test 2: Multi-turn tool use ===")
messages2 = messages + [
    result["message"],
    {"role": "tool", "content": json.dumps({"success": True, "tool": "open_application", "data": {"name": "Safari"}})}
]
resp2 = httpx.post(OLLAMA_URL, json={
    "model": "gemma4:12b-mlx",
    "messages": messages2,
    "tools": tools,
    "stream": False
}, timeout=120.0)
result2 = resp2.json()
print(json.dumps(result2, indent=2))

if result2.get("message", {}).get("tool_calls"):
    print("\n✅ Follow-up tool calls generated")
    for tc in result2["message"]["tool_calls"]:
        print(f"  Tool: {tc['function']['name']}")
        print(f"  Args: {tc['function']['arguments']}")

# Test 3: Memory usage
import subprocess
mem = subprocess.run(["ollama", "ps"], capture_output=True, text=True)
print(f"\n=== Memory Usage ===\n{mem.stdout}")

print("\n=== Test 3: Conversational (no tools) ===")
resp3 = httpx.post(OLLAMA_URL, json={
    "model": "gemma4:12b-mlx",
    "messages": [{"role": "user", "content": "What is a mutex? Answer briefly."}],
    "stream": False
}, timeout=120.0)
result3 = resp3.json()
print(f"Response: {result3.get('message', {}).get('content', 'N/A')[:500]}")
print(f"Eval count: {result3.get('eval_count', 'N/A')}")
print(f"Total duration: {result3.get('total_duration', 0) / 1e9:.2f}s")
