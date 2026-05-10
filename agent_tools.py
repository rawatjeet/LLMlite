"""
Tool-Using Agent (Custom JSON Action Block Parsing)

Demonstrates the simplest possible "agent in a loop" pattern. Unlike the
function-calling agents (which use the LLM's native `tool_calls` field),
this agent asks the LLM to emit a Markdown ```action JSON code block``` and
parses it manually with regex.

Pattern:
    user task -> LLM emits ```action {tool_name, args}``` -> we run it
              -> result fed back as the next user message
              -> repeat until the LLM returns the `terminate` action

Usage:
    python agent_tools.py
    python agent_tools.py --task "List Python files and read README"
    python agent_tools.py --task "Read main.py" --verbose --max-iterations 5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

from llmlite_common import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    call_with_retries,
    get_text,
    validate_api_key,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_markdown_block(response: str, block_type: str = "action") -> str:
    """Extract the contents of the first ```<block_type> ... ``` fenced block."""
    if "```" not in response:
        return response

    parts = response.split("```")
    if len(parts) < 2:
        return response

    code_block = parts[1].strip()
    if code_block.startswith(block_type):
        code_block = code_block[len(block_type):].strip()
    return code_block


def parse_action(response: str) -> Dict:
    """Parse the LLM response into a {tool_name, args} dictionary."""
    try:
        body = extract_markdown_block(response, "action")
        parsed = json.loads(body)
        if "tool_name" in parsed and "args" in parsed:
            return parsed
        return {
            "tool_name": "error",
            "args": {"message": "You must respond with a JSON tool invocation."},
        }
    except json.JSONDecodeError:
        return {
            "tool_name": "error",
            "args": {
                "message": "Invalid JSON. Wrap your response in a ```action ... ``` block.",
            },
        }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def list_files() -> List[str]:
    """List files in the current directory."""
    return sorted(os.listdir("."))


def read_file(file_name: str) -> str:
    """Read a file's contents (UTF-8)."""
    try:
        return Path(file_name).read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"Error: '{file_name}' not found."
    except UnicodeDecodeError:
        return f"Error: '{file_name}' is not a UTF-8 text file."
    except Exception as exc:
        return f"Error: {exc}"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

AGENT_RULES = [{
    "role": "system",
    "content": """\
You are an AI agent that can perform tasks by using available tools.

Available tools:

```json
{
    "list_files": {
        "description": "Lists all files in the current directory.",
        "parameters": {}
    },
    "read_file": {
        "description": "Reads the content of a file.",
        "parameters": {
            "file_name": {"type": "string", "description": "File to read."}
        }
    },
    "terminate": {
        "description": "Ends the agent loop and returns a summary message.",
        "parameters": {
            "message": {"type": "string", "description": "Final summary."}
        }
    }
}
```

If a user asks about files, list them before reading.
When done, call the `terminate` tool.

Important: every response MUST contain an action. Use this format:

<Stop and think step by step. Briefly describe your reasoning here.>

```action
{
    "tool_name": "<tool_name>",
    "args": {...}
}
```
"""
}]


def run_agent(
    user_task: str,
    *,
    model: str = DEFAULT_MODEL,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    verbose: bool = False,
) -> str:
    """Run the agent loop. Returns the terminate message (or last result)."""
    memory: List[Dict] = [{"role": "user", "content": user_task}]
    final_message = ""

    for iteration in range(1, max_iterations + 1):
        if verbose:
            print(f"\n--- Iteration {iteration}/{max_iterations} ---")

        prompt = AGENT_RULES + memory
        response = call_with_retries(
            model=model,
            messages=prompt,
            max_tokens=DEFAULT_MAX_TOKENS,
            verbose=verbose,
        )
        text = get_text(response)
        if verbose:
            print(f"Agent response:\n{text}\n")

        action = parse_action(text)
        tool_name = action["tool_name"]

        if tool_name == "list_files":
            result = {"result": list_files()}
        elif tool_name == "read_file":
            result = {"result": read_file(action["args"].get("file_name", ""))}
        elif tool_name == "error":
            result = {"error": action["args"].get("message", "Unknown error")}
        elif tool_name == "terminate":
            final_message = action["args"].get("message", "")
            print(f"\n{final_message}")
            return final_message
        else:
            result = {"error": f"Unknown action: {tool_name}"}

        print(f"Action result: {result}")

        memory.extend([
            {"role": "assistant", "content": text},
            {"role": "user", "content": json.dumps(result)},
        ])

    print("\nMax iterations reached without terminating.")
    return final_message


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tool-using agent with custom JSON action-block parsing.",
    )
    parser.add_argument("--task", type=str, help="Task to run (otherwise interactive)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--max-iterations", type=int, default=DEFAULT_MAX_ITERATIONS)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    validate_api_key()

    task = args.task or input("What would you like me to do? ").strip()
    if not task:
        print("No task provided.")
        return 1

    try:
        run_agent(
            task,
            model=args.model,
            max_iterations=args.max_iterations,
            verbose=args.verbose,
        )
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1
    except Exception as exc:
        print(f"\nFailed: {exc}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
