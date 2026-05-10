"""
Single LLM Call Demo (Functional-Programming Persona)

A tiny standalone script that asks the LLM to write a Python function in
functional-programming style. Used in early lessons to show how to set
a system "persona" via the system message.

Usage:
    python page1.py
    python page1.py --task "Write a function to swap dict keys and values"
"""

from __future__ import annotations

import argparse
import sys
from typing import Dict, List

from llmlite_common import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    call_with_retries,
    get_text,
    validate_api_key,
)


SYSTEM_PROMPT = (
    "You are an expert software engineer that prefers functional programming."
)


def run_once(user_task: str, *, model: str = DEFAULT_MODEL) -> str:
    """Send the task with the functional-programming system prompt and print the answer."""
    messages: List[Dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_task},
    ]
    response = call_with_retries(
        model=model,
        messages=messages,
        max_tokens=DEFAULT_MAX_TOKENS,
    )
    text = get_text(response)
    print(text)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Single LLM call with a functional-programming persona")
    parser.add_argument(
        "--task",
        type=str,
        default="Write a function to swap the keys and values in a dictionary.",
        help="The user task / prompt",
    )
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    args = parser.parse_args()

    validate_api_key()
    try:
        run_once(args.task, model=args.model)
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
