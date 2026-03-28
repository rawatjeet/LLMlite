# How to Build an LLM Agent: A Complete Guide

This guide walks you through the requirements, design decisions, and implementation steps for building an AI agent from scratch. Every concept here is demonstrated in the agents in this repository.

---

## Table of Contents

1. [What Is an Agent?](#what-is-an-agent)
2. [Requirements Checklist](#requirements-checklist)
3. [Choose Your Pattern](#choose-your-pattern)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Designing Tools](#designing-tools)
6. [The Agent Loop](#the-agent-loop)
7. [Memory and State](#memory-and-state)
8. [Error Handling and Safety](#error-handling-and-safety)
9. [Testing Your Agent](#testing-your-agent)
10. [Common Pitfalls](#common-pitfalls)
11. [Pattern Decision Flowchart](#pattern-decision-flowchart)

---

## What Is an Agent?

An agent is a program that uses an LLM to **decide what actions to take** in a loop. Unlike a simple chatbot (one prompt in, one response out), an agent:

- Receives a goal
- Reasons about what to do
- Executes actions (tools)
- Observes results
- Decides the next step
- Repeats until the goal is met or it gives up

The simplest way to think about it:

```
Agent = LLM + Tools + Loop + Memory
```

| Component | What it does | Example |
|-----------|-------------|---------|
| LLM | Makes decisions | "I should read this file to understand the code" |
| Tools | Takes actions | `read_file("main.py")` |
| Loop | Keeps going | While not done, ask LLM what to do next |
| Memory | Tracks context | Previous messages, tool results, state |

---

## Requirements Checklist

Before writing any code, answer these questions:

### 1. Define the Problem

- [ ] What task will the agent perform?
- [ ] What does "done" look like? (How does the agent know to stop?)
- [ ] What inputs does the user provide?
- [ ] What outputs should the agent produce?

### 2. Choose Infrastructure

- [ ] **LLM Provider**: Which model? (This project uses LiteLLM for provider-agnostic calls)
- [ ] **API Key**: How is authentication handled? (We use `.env` + `python-dotenv`)
- [ ] **Dependencies**: What packages are needed? (Keep minimal: `litellm`, `python-dotenv`)

### 3. Design the Tools

- [ ] What actions does the agent need? (read files, write files, search, execute code, etc.)
- [ ] What are the inputs/outputs for each tool?
- [ ] What are the safety boundaries? (read-only vs. write access, sandboxing)

### 4. Pick the Architecture

- [ ] Which agent pattern fits? (See the pattern guide below)
- [ ] How does the agent decide what to do? (Function calling vs. text parsing)
- [ ] How does the agent track progress? (Message history, explicit plan, session file)

### 5. Plan Safety

- [ ] Max iterations (prevent infinite loops)
- [ ] Timeouts on tool execution
- [ ] Input validation for tool arguments
- [ ] Cost awareness (track token usage)

---

## Choose Your Pattern

Each agent in this repository implements a different pattern. Here's when to use each:

### Simple Loop (`agent_loop_with_function_calling.py`)
**When**: Your task is straightforward - call tools until done.
**How it works**: LLM picks a function, you execute it, feed result back, repeat.
**Best for**: File operations, data gathering, simple automation.

### ReAct (`agent_react.py`)
**When**: You need the LLM to explain its reasoning before acting.
**How it works**: LLM outputs Thought → Action → Observation in a structured format.
**Best for**: Complex multi-step tasks, debugging, research tasks.

### Plan-then-Execute (`agent_planner.py`)
**When**: The task has many steps and order matters.
**How it works**: Phase 1: Generate a plan. Phase 2: Execute each step.
**Best for**: Refactoring, migrations, multi-file changes.

### Conversational (`agent_conversational.py`)
**When**: The user needs an ongoing dialogue with tool access.
**How it works**: Chat loop with persistent sessions and in-chat commands.
**Best for**: Interactive assistants, tutoring, exploration.

### Multi-Agent (`agent_multi.py`)
**When**: Different parts of the task need different expertise.
**How it works**: A router delegates sub-tasks to specialist agents.
**Best for**: Complex projects needing analysis + writing + coding.

### Self-Healing (`agent_self_healing.py`)
**When**: You need code that actually works, not just looks right.
**How it works**: Generate → Execute → If error, fix → Repeat.
**Best for**: Code generation, script automation, test creation.

### RAG (`agent_rag.py`)
**When**: Answering questions about large codebases or document sets.
**How it works**: Index files → Search for relevant chunks → Generate grounded answer.
**Best for**: Q&A over docs, code understanding, knowledge bases.

### Generator-Critic (`agent_critic.py`)
**When**: You want higher quality output through self-review.
**How it works**: Generate → Critique → Refine → Repeat.
**Best for**: Writing, code review, documentation, plans.

---

## Step-by-Step Implementation

Here's the exact process for building a new agent in this project:

### Step 1: Create the File

```
agent_<name>.py
```

Start with the standard boilerplate:

```python
"""
<Agent Name>

<One-paragraph description of what it does and the pattern it uses.>

Usage:
    python agent_<name>.py
    python agent_<name>.py --task "description"
    python agent_<name>.py --verbose
"""

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    raise RuntimeError(
        "Missing dependency: python-dotenv\n"
        "Install it by running: pip install -r requirements.txt"
    )

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from litellm import completion

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))
```

### Step 2: Define Your Tools

Tools are just Python functions. Each one must:
- Accept clear typed arguments
- Return a result (string for LLM consumption)
- Handle errors gracefully (return error messages, don't crash)

```python
TOOLS = {
    "read_file": {
        "function": read_file,
        "description": "Read the contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {"type": "string", "description": "Path to the file"}
            },
            "required": ["file_name"]
        }
    },
    # ... more tools
}
```

Two approaches for tool calling:

**A. Native Function Calling** (used in `agent_loop_with_function_calling.py`):
The LLM provider's built-in tool-use API. More reliable, but needs provider support.

```python
tools = [{"type": "function", "function": tool_def} for tool_def in TOOLS.values()]
response = completion(model=model, messages=messages, tools=tools)
# LLM returns tool_calls with name + arguments
```

**B. Text Parsing** (used in `agent_react.py`):
The LLM outputs structured text that you parse with regex. Works with any model.

```python
# LLM outputs:
# Thought: I need to read the file to understand the code
# Action: read_file
# Action Input: {"file_name": "main.py"}

action_match = re.search(r"Action:\s*(\w+)", response)
input_match = re.search(r"Action Input:\s*({.*})", response, re.DOTALL)
```

### Step 3: Write the System Prompt

The system prompt defines the agent's personality and rules. Critical elements:

```python
SYSTEM_PROMPT = """You are a [specific role].

Your task: [what the agent does]

Available tools:
[list each tool with description and when to use it]

Rules:
1. [How to decide which tool to use]
2. [When to stop / what "done" means]
3. [Output format expectations]
4. [Safety constraints]
"""
```

Tips for effective system prompts:
- Be specific about the output format the agent should use
- List all available tools with examples
- Define clear termination conditions
- Set boundaries (what the agent should NOT do)

### Step 4: Build the Agent Loop

Every agent follows this core pattern:

```python
def run_agent(task: str, model: str, max_iterations: int = 10) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for i in range(max_iterations):
        # 1. Call the LLM
        response = completion(model=model, messages=messages, tools=tools)
        assistant_msg = response.choices[0].message

        # 2. Check for termination
        if should_stop(assistant_msg):
            return extract_final_answer(assistant_msg)

        # 3. Execute tools
        tool_results = execute_tools(assistant_msg)

        # 4. Feed results back as memory
        messages.append(assistant_msg)
        messages.append(tool_results)

        # 5. Print progress
        print(f"Step {i+1}: {summarize(assistant_msg)}")

    return "Max iterations reached"
```

### Step 5: Add the CLI

```python
def main():
    parser = argparse.ArgumentParser(description="Your Agent")
    parser.add_argument("--task", type=str, help="Task description")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--max-iterations", type=int, default=10)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # Validate API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key found.")
        return 1

    # Interactive input if no --task
    if not args.task:
        args.task = input("Your task: ").strip()

    return run_agent(args.task, args.model, args.max_iterations)

if __name__ == "__main__":
    sys.exit(main())
```

### Step 6: Add Documentation

Create `agent_<name>_readme.md` with:
- Overview and architecture diagram
- Prerequisites and quick start
- Example sessions
- Configuration options
- Troubleshooting

---

## Designing Tools

### The Five Essential Tools

Most agents need some subset of these:

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `list_files` | See what's available | directory path | file/folder names |
| `read_file` | Get content | file path | file contents |
| `write_file` | Create/modify files | path + content | success/failure |
| `search_files` | Find relevant files | pattern/query | matching paths |
| `finish` | Signal completion | final message | (terminates loop) |

### Tool Design Principles

1. **Atomic**: Each tool does ONE thing. Don't combine read+write.
2. **Descriptive**: The description tells the LLM WHEN to use it, not just what it does.
3. **Safe by default**: Read-only tools need no guard. Write tools need confirmation or sandboxing.
4. **Error-tolerant**: Return error messages as strings, never raise exceptions that kill the loop.
5. **Bounded**: Limit output size (truncate large files), set timeouts on execution.

### Adding a New Tool

```python
def my_new_tool(param1: str, param2: int = 10) -> str:
    """Tool that does X. Returns result as string."""
    try:
        result = do_the_thing(param1, param2)
        return f"Success: {result}"
    except Exception as e:
        return f"Error: {e}"

# Register it in the tools dict
TOOLS["my_new_tool"] = {
    "function": my_new_tool,
    "description": "Does X when you need to Y. Use this when Z.",
    "parameters": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "What this is"},
            "param2": {"type": "integer", "description": "How many", "default": 10},
        },
        "required": ["param1"],
    },
}
```

---

## Memory and State

### Short-term Memory (Message History)

Every agent maintains a conversation history:

```python
messages = [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "task"},
    {"role": "assistant", "content": "thinking..."},
    {"role": "tool", "content": "result..."},
    # ... grows with each iteration
]
```

**Problem**: This grows unbounded. Solutions:
- Sliding window: Keep only the last N messages
- Summarization: Periodically summarize older messages
- Max iterations: Hard limit prevents runaway growth

### Long-term Memory (Session Persistence)

For multi-session agents (like `agent_conversational.py`):

```python
import json
from pathlib import Path

SESSION_DIR = Path(".agent_sessions")

def save_session(session_id: str, messages: list):
    SESSION_DIR.mkdir(exist_ok=True)
    path = SESSION_DIR / f"{session_id}.json"
    path.write_text(json.dumps(messages, indent=2))

def load_session(session_id: str) -> list:
    path = SESSION_DIR / f"{session_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return []
```

### Structured State (Plans, Checklists)

For plan-based agents (`agent_planner.py`):

```python
plan = [
    {"step": 1, "task": "Read the file", "status": "done", "result": "..."},
    {"step": 2, "task": "Find the bug", "status": "in_progress", "result": None},
    {"step": 3, "task": "Fix the bug", "status": "pending", "result": None},
]
```

This gives the LLM explicit awareness of what's been done and what's left.

---

## Error Handling and Safety

### LLM Call Errors

```python
from litellm import exceptions as litellm_exceptions
import time

def safe_completion(model, messages, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return completion(model=model, messages=messages, **kwargs)
        except litellm_exceptions.RateLimitError:
            wait = 2 ** attempt
            print(f"Rate limited, waiting {wait}s...")
            time.sleep(wait)
        except litellm_exceptions.AuthenticationError:
            raise  # Don't retry auth failures
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"LLM error (attempt {attempt+1}): {e}")
            time.sleep(1)
```

### Tool Execution Safety

```python
# For file operations: validate paths
def read_file(file_name: str) -> str:
    path = Path(file_name).resolve()

    # Prevent directory traversal
    if ".." in str(path):
        return "Error: path traversal not allowed"

    # Check size before reading
    if path.stat().st_size > 1_000_000:
        return "Error: file too large (>1MB)"

    return path.read_text(encoding="utf-8", errors="replace")

# For shell commands: use an allowlist
ALLOWED_COMMANDS = {"ls", "cat", "head", "wc", "grep", "find", "python"}

def shell_command(command: str) -> str:
    executable = command.split()[0]
    if executable not in ALLOWED_COMMANDS:
        return f"Error: '{executable}' is not in the allowed command list"
    # ... execute with timeout
```

### Infinite Loop Prevention

```python
MAX_ITERATIONS = 20

for i in range(MAX_ITERATIONS):
    response = call_llm(messages)
    if is_done(response):
        break
else:
    print(f"Warning: reached max iterations ({MAX_ITERATIONS})")
```

---

## Testing Your Agent

### Smoke Test

Run the simplest possible task to verify the loop works:

```bash
python agent_<name>.py --task "List all Python files in the current directory"
```

### Stress Tests

| Test | What it catches |
|------|----------------|
| Empty input | `--task ""` should error gracefully |
| Very long input | Large prompts shouldn't crash |
| Invalid tool args | LLM sometimes sends bad JSON |
| Network failure | Disconnect during LLM call |
| Tool failure | File not found, permission denied |
| Infinite loop | Agent that never calls finish |

### Verbose Mode

Always support `--verbose` to see:
- Full LLM responses (not just extracted actions)
- Tool inputs and outputs
- Token counts and costs
- Timing information

---

## Common Pitfalls

### 1. No Termination Condition
**Symptom**: Agent loops forever.
**Fix**: Always include a `finish`/`terminate` tool AND a max iteration guard.

### 2. LLM Ignores Tools
**Symptom**: LLM generates text instead of tool calls.
**Fix**: Be more explicit in the system prompt. Add "You MUST use a tool on every turn."

### 3. Context Window Overflow
**Symptom**: LLM starts hallucinating or returns errors after many iterations.
**Fix**: Truncate tool results, summarize old messages, or use a sliding window.

### 4. JSON Parse Failures
**Symptom**: `json.loads()` crashes on LLM output.
**Fix**: Always wrap parsing in try/except. Use regex as fallback. Add "Output valid JSON only" to the prompt.

### 5. Cost Explosion
**Symptom**: $50 API bill from one test run.
**Fix**: Set `max_tokens`, limit iterations, use cheaper models for testing, log token usage.

### 6. Tool Result Too Large
**Symptom**: Reading a 10,000-line file fills the context window.
**Fix**: Truncate tool results to a maximum size (e.g., first 200 lines).

### 7. Agent Takes Wrong Path
**Symptom**: Agent uses wrong tools or does irrelevant things.
**Fix**: Improve the system prompt, add better tool descriptions with "use when" hints, add few-shot examples to the prompt.

---

## Pattern Decision Flowchart

Use this to decide which pattern to implement:

```
Is the task a single question about existing data?
  YES → RAG Agent (agent_rag.py)
  NO  ↓

Does the task need code that must actually execute?
  YES → Self-Healing Agent (agent_self_healing.py)
  NO  ↓

Does quality matter more than speed?
  YES → Generator-Critic Agent (agent_critic.py)
  NO  ↓

Does the task have many ordered steps?
  YES → Plan-then-Execute Agent (agent_planner.py)
  NO  ↓

Does the task need multiple types of expertise?
  YES → Multi-Agent (agent_multi.py)
  NO  ↓

Does the user need ongoing conversation?
  YES → Conversational Agent (agent_conversational.py)
  NO  ↓

Does the LLM need to explain its reasoning?
  YES → ReAct Agent (agent_react.py)
  NO  → Simple Loop (agent_loop_with_function_calling.py)
```

---

## Quick Reference: File Naming Convention

| File | Purpose |
|------|---------|
| `agent_<name>.py` | Agent implementation |
| `agent_<name>_readme.md` | Documentation for that agent |
| `agent_tools.py` | Shared tool definitions |
| `tool_decorators.py` | `@register_tool` decorator utility |
| `template.py` | Minimal starter boilerplate |
| `.env` | API keys (never commit) |
| `requirements.txt` | Python dependencies |

---

## Putting It All Together

Building an agent is really just five decisions:

1. **What tools does it need?** (read, write, search, execute, finish)
2. **How does it decide?** (function calling vs. text parsing)
3. **How does it track progress?** (messages, plan, session)
4. **How does it stop?** (finish tool, max iterations, success criteria)
5. **How does it recover?** (retry, self-heal, critic, or fail gracefully)

Start with the simplest pattern that could work. You can always make it more sophisticated later. Every agent in this repo follows the same core structure - the only difference is how the LLM's output is interpreted and what happens between iterations.
