"""
Agent Loop with Native Function Calling (Level 4, basic)

Puts `llm_function_call.py` inside a loop. The LLM keeps picking tools
until it calls `terminate(message)` or hits the iteration cap.

Usage:
    python agent_loop_with_function_calling.py
    python agent_loop_with_function_calling.py --task "List Python files"
    python agent_loop_with_function_calling.py --max-iterations 5 --verbose
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
    validate_api_key,
)


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


def terminate(message: str) -> None:
    """Stop the loop and print the final summary."""
    print(f"Termination message: {message}")


TOOL_FUNCTIONS = {
    "list_files": list_files,
    "read_file": read_file,
    "terminate": terminate,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Returns a list of files in the directory.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the content of a specified file in the directory.",
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
            "description": (
                "Terminates the conversation. No further actions or interactions are "
                "possible after this. Prints the provided message for the user."
            ),
            "parameters": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        },
    },
]

AGENT_RULES = [{
    "role": "system",
    "content": (
        "You are an AI agent that can perform tasks by using available tools.\n\n"
        "If a user asks about files, documents, or content, first list the files "
        "before reading them.\n\n"
        "When you are done, terminate the conversation by using the 'terminate' "
        "tool and I will provide the results to the user."
    ),
}]


def run_agent(
    user_task: str,
    *,
    model: str = DEFAULT_MODEL,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    verbose: bool = False,
) -> None:
    """Run the function-calling agent loop."""
    memory: List[Dict] = [{"role": "user", "content": user_task}]

    for iteration in range(1, max_iterations + 1):
        if verbose:
            print(f"\n--- Iteration {iteration}/{max_iterations} ---")

        messages = AGENT_RULES + memory
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
            print(f"Response: {message.content}")
            return

        tool = tool_calls[0]
        tool_name = tool.function.name
        tool_args = json.loads(tool.function.arguments)
        action = {"tool_name": tool_name, "args": tool_args}

        if tool_name == "terminate":
            print(f"Termination message: {tool_args.get('message', '')}")
            return

        if tool_name in TOOL_FUNCTIONS:
            try:
                result = {"result": TOOL_FUNCTIONS[tool_name](**tool_args)}
            except Exception as exc:
                result = {"error": f"Error executing {tool_name}: {exc}"}
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        print(f"Executing: {tool_name} with args {tool_args}")
        print(f"Result   : {result}")

        memory.extend([
            {"role": "assistant", "content": json.dumps(action)},
            {"role": "user", "content": json.dumps(result)},
        ])

    print(f"\nMax iterations ({max_iterations}) reached without terminating.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent loop with native function calling")
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


if __name__ == "__main__":
    sys.exit(main())
