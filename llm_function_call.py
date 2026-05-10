"""
Single-Shot Native Function Calling (Level 3, simplest form)

Sends one tool list + one user request to the LLM and runs whichever tool
the LLM picks. No loop, no follow-up — this is the absolute minimum form
of "tool use" with a modern LLM.

For the looping version, see `agent_loop_with_function_calling.py`.

Usage:
    python llm_function_call.py
    python llm_function_call.py --task "Read the README"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

from llmlite_common import (
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


TOOL_FUNCTIONS = {
    "list_files": list_files,
    "read_file": read_file,
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
]

AGENT_RULES = [{
    "role": "system",
    "content": (
        "You are an AI agent that can perform tasks by using available tools. "
        "If a user asks about files, documents, or content, first list the "
        "files before reading them."
    ),
}]


def run_once(user_task: str, *, model: str = DEFAULT_MODEL) -> None:
    """Make a single tool-calling LLM request and execute the chosen tool."""
    messages = AGENT_RULES + [{"role": "user", "content": user_task}]

    response = call_with_retries(
        model=model,
        messages=messages,
        tools=TOOLS,
        max_tokens=DEFAULT_MAX_TOKENS,
    )

    message = response.choices[0].message
    tool_calls = getattr(message, "tool_calls", None)

    if not tool_calls:
        print("LLM did not request a tool. Response:")
        print(message.content)
        return

    tool = tool_calls[0]
    tool_name = tool.function.name
    tool_args = json.loads(tool.function.arguments)
    result = TOOL_FUNCTIONS[tool_name](**tool_args)

    print(f"Tool Name : {tool_name}")
    print(f"Tool Args : {tool_args}")
    print(f"Result    : {result}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Single-shot native function calling demo")
    parser.add_argument("--task", type=str, help="Task to run (otherwise interactive)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    args = parser.parse_args()

    validate_api_key()

    task = args.task or input("What would you like me to do? ").strip()
    if not task:
        print("No task provided.")
        return 1

    try:
        run_once(task, model=args.model)
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
