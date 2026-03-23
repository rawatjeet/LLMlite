"""
ReAct Agent (Reasoning + Acting)

Implements the ReAct pattern where the LLM explicitly produces:
  Thought  -> internal reasoning about the situation
  Action   -> a tool invocation
  Observation -> the result fed back to the LLM

This is one of the most effective and well-studied agent patterns.
Unlike the basic agent loop, the LLM is forced to articulate its
reasoning *before* choosing an action, which significantly improves
decision quality.

Usage:
    python agent_react.py
    python agent_react.py --task "Summarize all Python files in this project"
    python agent_react.py --verbose --max-iterations 15
"""

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    raise RuntimeError(
        "Missing dependency: python-dotenv\n"
        "Install it by running: pip install -r requirements.txt"
    )

import os
import re
import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from litellm import completion

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_ITERATIONS = int(os.getenv("DEFAULT_MAX_ITERATIONS", "15"))
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def list_files(directory: str = ".") -> str:
    """List files and directories at the given path."""
    try:
        p = Path(directory)
        if not p.exists():
            return f"Error: '{directory}' does not exist."
        items = sorted(item.name + ("/" if item.is_dir() else "") for item in p.iterdir())
        return "\n".join(items) if items else "(empty directory)"
    except Exception as e:
        return f"Error: {e}"


def read_file(file_name: str) -> str:
    """Read the full text content of a file (max 50 KB)."""
    try:
        p = Path(file_name)
        if not p.exists():
            return f"Error: '{file_name}' not found."
        if not p.is_file():
            return f"Error: '{file_name}' is not a file."
        size = p.stat().st_size
        if size > 50_000:
            return f"Error: File too large ({size} bytes). Max 50 KB."
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Error: '{file_name}' is not a text file."
    except Exception as e:
        return f"Error: {e}"


def write_file(file_name: str, content: str) -> str:
    """Write text content to a file (creates or overwrites)."""
    try:
        Path(file_name).write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} characters to '{file_name}'."
    except Exception as e:
        return f"Error: {e}"


def search_in_file(file_name: str, pattern: str) -> str:
    """Search for a regex pattern inside a file and return matching lines."""
    try:
        text = Path(file_name).read_text(encoding="utf-8")
        matches = [
            f"  L{i+1}: {line}"
            for i, line in enumerate(text.splitlines())
            if re.search(pattern, line)
        ]
        if not matches:
            return f"No matches for '{pattern}' in {file_name}."
        return f"{len(matches)} match(es) in {file_name}:\n" + "\n".join(matches[:30])
    except Exception as e:
        return f"Error: {e}"


def shell_command(command: str) -> str:
    """Run a safe read-only shell command (ls, cat, wc, head, find, grep)."""
    import subprocess

    ALLOWED_PREFIXES = ("ls", "dir", "cat", "head", "tail", "wc", "find", "grep", "type", "echo")
    cmd_lower = command.strip().lower()
    if not any(cmd_lower.startswith(p) for p in ALLOWED_PREFIXES):
        return f"Error: Only read-only commands are allowed ({', '.join(ALLOWED_PREFIXES)})."

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=10
        )
        output = result.stdout + result.stderr
        return output.strip()[:5000] if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out (10s limit)."
    except Exception as e:
        return f"Error: {e}"


TOOL_REGISTRY: Dict[str, Callable] = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "search_in_file": search_in_file,
    "shell_command": shell_command,
}

TOOL_DESCRIPTIONS = """Available tools (use EXACTLY one per action):

1. list_files(directory: str = ".") -> lists files/dirs at the path
2. read_file(file_name: str)       -> reads text content of a file
3. write_file(file_name: str, content: str) -> writes text to a file
4. search_in_file(file_name: str, pattern: str) -> regex search inside a file
5. shell_command(command: str)      -> run a read-only shell command
6. finish(answer: str)             -> provide the final answer and stop"""


# ---------------------------------------------------------------------------
# ReAct prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""You are a ReAct agent. You solve tasks by interleaving Thought, Action, and Observation steps.

{TOOL_DESCRIPTIONS}

You MUST follow this format on every turn:

Thought: <your reasoning about the current situation and what to do next>
Action: <tool_name>(<arg1>, <arg2>, ...)
... then you will receive an Observation with the result.

Rules:
- Always start with a Thought.
- Each turn has exactly ONE Thought and ONE Action.
- When the task is fully complete, use: Action: finish("<your final answer>")
- Be thorough: gather evidence before concluding.
- If an action fails, reason about why and try a different approach.
"""


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def parse_react_response(text: str) -> Dict[str, Any]:
    """
    Parse the LLM output to extract the Thought and Action.

    Returns dict with keys: thought, tool_name, args
    """
    thought = ""
    thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|\Z)", text, re.DOTALL)
    if thought_match:
        thought = thought_match.group(1).strip()

    action_match = re.search(r"Action:\s*(\w+)\((.*)?\)\s*$", text, re.MULTILINE | re.DOTALL)
    if not action_match:
        return {"thought": thought, "tool_name": "error", "args": {}}

    tool_name = action_match.group(1).strip()
    raw_args = (action_match.group(2) or "").strip()

    args = _parse_action_args(tool_name, raw_args)
    return {"thought": thought, "tool_name": tool_name, "args": args}


def _parse_action_args(tool_name: str, raw: str) -> Dict[str, Any]:
    """Best-effort extraction of keyword or positional arguments."""
    if not raw:
        return {}

    # Try to interpret as JSON object first
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # Try keyword style: key="value", key2="value2"
    kw_pairs = re.findall(r'(\w+)\s*=\s*(".*?"|\'.*?\'|[^,]+)', raw)
    if kw_pairs:
        result = {}
        for k, v in kw_pairs:
            v = v.strip().strip("\"'")
            result[k] = v
        return result

    # Fall back to positional mapping
    import inspect
    if tool_name in TOOL_REGISTRY:
        sig = inspect.signature(TOOL_REGISTRY[tool_name])
        param_names = list(sig.parameters.keys())
    elif tool_name == "finish":
        param_names = ["answer"]
    else:
        param_names = ["arg0"]

    parts = _split_args(raw)
    result = {}
    for i, part in enumerate(parts):
        key = param_names[i] if i < len(param_names) else f"arg{i}"
        result[key] = part.strip().strip("\"'")
    return result


def _split_args(s: str) -> List[str]:
    """Split a comma-separated argument string respecting quotes."""
    parts, current, depth, in_quote = [], [], 0, None
    for ch in s:
        if ch in ('"', "'") and in_quote is None:
            in_quote = ch
        elif ch == in_quote:
            in_quote = None
        elif ch == "(" and in_quote is None:
            depth += 1
        elif ch == ")" and in_quote is None:
            depth -= 1
        elif ch == "," and depth == 0 and in_quote is None:
            parts.append("".join(current))
            current = []
            continue
        current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def run_react_agent(
    task: str,
    model: str = DEFAULT_MODEL,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    verbose: bool = False,
) -> str:
    """
    Execute the ReAct loop.

    Returns the final answer string.
    """
    print("\n" + "=" * 70)
    print("  REACT AGENT  (Thought -> Action -> Observation)")
    print("=" * 70)
    print(f"Task : {task}")
    print(f"Model: {model}  |  Max iterations: {max_iterations}\n")

    messages: List[Dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Task: {task}"},
    ]

    for step in range(1, max_iterations + 1):
        print(f"--- Step {step} ---")

        response = completion(
            model=model,
            messages=messages,
            max_tokens=DEFAULT_MAX_TOKENS,
        )
        llm_text = response.choices[0].message.content.strip()

        parsed = parse_react_response(llm_text)
        thought = parsed["thought"]
        tool_name = parsed["tool_name"]
        args = parsed["args"]

        if verbose:
            print(f"[LLM raw]\n{llm_text}\n")
        print(f"Thought: {thought[:300]}")
        print(f"Action : {tool_name}({args})")

        # Finish
        if tool_name == "finish":
            answer = args.get("answer", str(args))
            print(f"\n{'=' * 70}")
            print("  TASK COMPLETE")
            print(f"{'=' * 70}")
            print(f"Answer:\n{answer}\n")
            return answer

        # Execute tool
        if tool_name in TOOL_REGISTRY:
            try:
                observation = TOOL_REGISTRY[tool_name](**args)
            except Exception as e:
                observation = f"Error executing {tool_name}: {e}"
        else:
            observation = f"Unknown tool '{tool_name}'. Choose from: {', '.join(TOOL_REGISTRY)}, finish"

        display_obs = observation[:500] + "..." if len(observation) > 500 else observation
        print(f"Observation: {display_obs}\n")

        messages.append({"role": "assistant", "content": llm_text})
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    print("\nMax iterations reached without finishing.")
    return "Agent did not finish within the iteration limit."


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ReAct Agent - Reasoning + Acting pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_react.py
  python agent_react.py --task "Find and summarize README files"
  python agent_react.py --task "What functions are defined in agent_tools.py?" --verbose
  python agent_react.py --max-iterations 20

Pattern explained:
  The ReAct pattern forces the LLM to produce explicit reasoning (Thought)
  before every action, leading to more reliable multi-step problem solving.
  See: https://arxiv.org/abs/2210.03629
""",
    )
    parser.add_argument("--task", type=str, help="Task for the agent")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--max-iterations", type=int, default=DEFAULT_MAX_ITERATIONS)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key found. Set GEMINI_API_KEY or OPENAI_API_KEY in .env")
        return 1

    if args.task:
        task = args.task
    else:
        print("\nWhat would you like the ReAct agent to do?")
        print("Example: 'List all Python files and summarize what each one does'\n")
        task = input("Your task: ").strip()
        if not task:
            print("No task provided.")
            return 1

    try:
        run_react_agent(
            task=task,
            model=args.model,
            max_iterations=args.max_iterations,
            verbose=args.verbose,
        )
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1
    except Exception as e:
        print(f"\nFailed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
