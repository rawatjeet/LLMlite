"""
Agent Template — Starter Skeleton

Copy this file to `agent_<name>.py` and fill in:
  - the module docstring
  - the SYSTEM_PROMPT
  - your tool functions and TOOL_FUNCTIONS / TOOLS specs
  - the body of run_agent() if you need anything beyond the default loop

Follows the conventions in `.cursor/rules/agent-development.mdc`:
  - Module docstring up top
  - DEFAULT_MODEL pulled from env (via llmlite_common)
  - validate_api_key() before any LLM call
  - argparse CLI with --task / --model / --max-iterations / --verbose
  - Max-iteration guard so the loop can never run forever
  - Graceful Ctrl-C handling
  - sys.exit(main()) on the way out

Usage:
    python template.py --task "List Python files"
    python template.py --task "Read README" --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List

from llmlite_common import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    call_with_retries,
    validate_api_key,
)


# ---------------------------------------------------------------------------
# Tools — replace with your own
# ---------------------------------------------------------------------------

def list_files(directory: str = ".") -> str:
    """List files and folders in a directory."""
    try:
        items = sorted(p.name + ("/" if p.is_dir() else "") for p in Path(directory).iterdir())
        return "\n".join(items) if items else "(empty)"
    except Exception as exc:
        return f"Error: {exc}"


def read_file(file_name: str) -> str:
    """Read the UTF-8 contents of a file (50 KB cap)."""
    try:
        path = Path(file_name)
        if not path.is_file():
            return f"Error: '{file_name}' not found."
        if path.stat().st_size > 50_000:
            return f"Error: file too large ({path.stat().st_size} bytes; max 50 KB)."
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Error: '{file_name}' is not a UTF-8 text file."
    except Exception as exc:
        return f"Error: {exc}"


TOOL_FUNCTIONS: Dict[str, Callable] = {
    "list_files": list_files,
    "read_file": read_file,
}

TOOLS: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {"directory": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file.",
            "parameters": {
                "type": "object",
                "properties": {"file_name": {"type": "string"}},
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "terminate",
            "description": "End the agent loop and return a summary message.",
            "parameters": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are an AI agent that can solve tasks by calling tools.\n"
    "When the task is complete, call the `terminate` tool with a short summary."
)


def run_agent(
    user_task: str,
    *,
    model: str = DEFAULT_MODEL,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    verbose: bool = False,
) -> str:
    """Standard agent loop: pick tool -> execute -> feed result back -> repeat."""
    memory: List[Dict] = [{"role": "user", "content": user_task}]
    final = ""

    for iteration in range(1, max_iterations + 1):
        if verbose:
            print(f"\n--- Iteration {iteration}/{max_iterations} ---")

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + memory
        response = call_with_retries(
            model=model,
            messages=messages,
            tools=TOOLS,
            max_tokens=DEFAULT_MAX_TOKENS,
            verbose=verbose,
        )

        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)

        if not tool_calls:
            final = message.content or ""
            print(f"\nResponse: {final}")
            return final

        tool = tool_calls[0]
        name = tool.function.name
        args = json.loads(tool.function.arguments)

        if name == "terminate":
            final = args.get("message", "")
            print(f"\n{final}")
            return final

        if name in TOOL_FUNCTIONS:
            try:
                result = {"result": TOOL_FUNCTIONS[name](**args)}
            except Exception as exc:
                result = {"error": f"{name} failed: {exc}"}
        else:
            result = {"error": f"Unknown tool: {name}"}

        if verbose:
            print(f"Tool: {name}({args})")
            print(f"Result: {str(result)[:300]}")

        memory.extend([
            {"role": "assistant", "content": json.dumps({"tool_name": name, "args": args})},
            {"role": "user", "content": json.dumps(result)},
        ])

    print(f"\nMax iterations ({max_iterations}) reached without terminating.")
    return final


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Agent template")
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
