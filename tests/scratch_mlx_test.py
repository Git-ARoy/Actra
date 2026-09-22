import json
from mlx_lm import load, generate

model_name = "mlx-community/gemma-4-12b-it-4bit"
model, tokenizer = load(model_name)

# Define tools
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
    }
]

messages = [
    {"role": "system", "content": "You are Actra, a macOS computer-use AI agent. Use the provided tools to accomplish tasks."},
    {"role": "user", "content": "Open Safari and search for iQOO 15"}
]

# Use apply_chat_template with tools
prompt = tokenizer.apply_chat_template(
    messages,
    tools=tools,
    add_generation_prompt=True,
    tokenize=False
)
print("=== Prompt with tools ===")
print(prompt[:2000])
print("...")

# Generate
response = generate(model, tokenizer, prompt=prompt, max_tokens=500, verbose=True)
print("\n=== Raw Response ===")
print(response)

# Check if response contains tool calls
if "tool_call" in response.lower() or "function" in response.lower() or "open_application" in response or "safari_search" in response:
    print("\n✅ Tool call detected in response")
else:
    print("\n⚠️ No clear tool call pattern detected")
