"""
Plan-and-Execute Agent

Implements a two-phase agent pattern:
  Phase 1 (Plan)    -> LLM creates a step-by-step plan for the task
  Phase 2 (Execute) -> LLM executes each step using tools, checking off items

This is more structured than ReAct: the agent commits to a plan upfront,
reducing aimless exploration. The plan can be revised mid-execution if
a step fails or new information emerges.

Usage:
    python agent_planner.py
    python agent_planner.py --task "Analyze this project and list all function names"
    python agent_planner.py --verbose
"""

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    raise RuntimeError(
        "Missing dependency: python-dotenv\n"
        "Install it by running: pip install -r requirements.txt"
    )

import os
import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from litellm import completion

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))


# ---------------------------------------------------------------------------
# Tools (same set as the other agents for consistency)
# ---------------------------------------------------------------------------

def list_files(directory: str = ".") -> str:
    try:
        p = Path(directory)
        items = sorted(item.name + ("/" if item.is_dir() else "") for item in p.iterdir())
        return "\n".join(items) if items else "(empty)"
    except Exception as e:
        return f"Error: {e}"


def read_file(file_name: str) -> str:
    try:
        p = Path(file_name)
        if not p.is_file():
            return f"Error: '{file_name}' is not a file or does not exist."
        if p.stat().st_size > 50_000:
            return f"Error: File too large (>{50_000} bytes)."
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error: {e}"


def write_file(file_name: str, content: str) -> str:
    try:
        Path(file_name).write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to '{file_name}'."
    except Exception as e:
        return f"Error: {e}"


def search_files(pattern: str, directory: str = ".") -> str:
    try:
        matches = sorted(str(p.name) for p in Path(directory).glob(pattern) if p.is_file())
        return "\n".join(matches) if matches else "No files matched."
    except Exception as e:
        return f"Error: {e}"


TOOL_FUNCTIONS: Dict[str, Callable] = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "search_files": search_files,
}

TOOLS_SPEC: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory path (default '.')"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the text content of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "File path to read"}
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["file_name", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files matching a glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern (e.g. '*.py')"},
                    "directory": {"type": "string", "description": "Search directory"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mark_step_done",
            "description": "Mark the current plan step as done and provide a brief result summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "step_result": {"type": "string", "description": "What was accomplished in this step"}
                },
                "required": ["step_result"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "Declare the overall task complete and provide the final answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string", "description": "The comprehensive final answer"}
                },
                "required": ["answer"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Phase 1: Planning
# ---------------------------------------------------------------------------

PLAN_SYSTEM_PROMPT = """You are a planning assistant. Given a user task, create a clear numbered plan.

Rules:
1. Break the task into 3-8 concrete, actionable steps.
2. Each step should be something that can be done with the available tools
   (list_files, read_file, write_file, search_files).
3. The last step should always be synthesizing results into a final answer.
4. Output ONLY a JSON array of step strings. No commentary.

Example output:
["List Python files in the project", "Read main.py to understand entry point", "Read agent_tools.py to understand tool system", "Compile a summary of the project architecture"]
"""


def generate_plan(task: str, model: str, verbose: bool = False) -> List[str]:
    """Ask the LLM to produce a step-by-step plan."""
    messages = [
        {"role": "system", "content": PLAN_SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    resp = completion(model=model, messages=messages, max_tokens=1024)
    raw = resp.choices[0].message.content.strip()

    if verbose:
        print(f"[Plan raw]\n{raw}\n")

    # Extract JSON array
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        plan = json.loads(raw)
        if isinstance(plan, list) and all(isinstance(s, str) for s in plan):
            return plan
    except json.JSONDecodeError:
        pass

    # Fallback: split by numbered lines
    import re
    steps = re.findall(r"\d+[.)]\s*(.+)", raw)
    return steps if steps else [f"Complete the task: {task}"]


# ---------------------------------------------------------------------------
# Phase 2: Execution
# ---------------------------------------------------------------------------

EXECUTE_SYSTEM_PROMPT = """You are an execution agent carrying out a plan step by step.

You have these tools available (provided via function calling):
- list_files, read_file, write_file, search_files
- mark_step_done: call this when the current step is accomplished
- finish: call this when ALL steps are done, with a comprehensive final answer

Current plan (steps marked [DONE] are already completed):
{plan_display}

You are currently working on: Step {current_step}
"{step_description}"

Previous step results:
{step_results}

Use the tools to accomplish this step, then call mark_step_done with what you found/did.
If all steps are done, call finish with the final answer.
"""


def execute_step(
    step_idx: int,
    steps: List[str],
    step_results: List[str],
    memory: List[Dict],
    model: str,
    verbose: bool = False,
    max_tool_calls: int = 10,
) -> Optional[str]:
    """
    Execute a single plan step. Returns the step result, or None if
    the agent called finish (meaning the whole task is done).
    """
    plan_display = ""
    for i, s in enumerate(steps):
        prefix = "[DONE]" if i < step_idx else "[TODO]" if i > step_idx else "[>>>]"
        plan_display += f"  {prefix} {i + 1}. {s}\n"

    results_display = ""
    for i, r in enumerate(step_results):
        results_display += f"  Step {i + 1}: {r}\n"
    if not results_display:
        results_display = "  (none yet)\n"

    system_content = EXECUTE_SYSTEM_PROMPT.format(
        plan_display=plan_display,
        current_step=step_idx + 1,
        step_description=steps[step_idx],
        step_results=results_display,
    )

    messages = [{"role": "system", "content": system_content}] + memory

    for call_num in range(max_tool_calls):
        resp = completion(model=model, messages=messages, tools=TOOLS_SPEC, max_tokens=DEFAULT_MAX_TOKENS)

        if not resp.choices[0].message.tool_calls:
            text = resp.choices[0].message.content or ""
            if verbose:
                print(f"  [Text response]: {text[:300]}")
            messages.append({"role": "assistant", "content": text})
            continue

        tool_call = resp.choices[0].message.tool_calls[0]
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)

        if verbose:
            print(f"  [Tool call #{call_num + 1}]: {fn_name}({fn_args})")

        if fn_name == "finish":
            return None  # signals overall completion

        if fn_name == "mark_step_done":
            return fn_args.get("step_result", "Step completed.")

        if fn_name in TOOL_FUNCTIONS:
            try:
                result = TOOL_FUNCTIONS[fn_name](**fn_args)
            except Exception as e:
                result = f"Error: {e}"
        else:
            result = f"Unknown tool: {fn_name}"

        display = result[:400] + "..." if len(result) > 400 else result
        print(f"    -> {fn_name}: {display}")

        action_summary = json.dumps({"tool": fn_name, "args": fn_args})
        messages.append({"role": "assistant", "content": action_summary})
        messages.append({"role": "user", "content": f"Tool result:\n{result}"})

    return "Step reached max tool calls without completing."


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_planner_agent(
    task: str,
    model: str = DEFAULT_MODEL,
    verbose: bool = False,
) -> str:
    print("\n" + "=" * 70)
    print("  PLAN-AND-EXECUTE AGENT")
    print("=" * 70)
    print(f"Task : {task}")
    print(f"Model: {model}\n")

    # Phase 1: Generate plan
    print("Phase 1: PLANNING")
    print("-" * 40)
    steps = generate_plan(task, model, verbose)
    for i, step in enumerate(steps):
        print(f"  {i + 1}. {step}")
    print()

    # Phase 2: Execute each step
    print("Phase 2: EXECUTION")
    print("-" * 40)

    step_results: List[str] = []
    memory: List[Dict] = [{"role": "user", "content": task}]
    final_answer = None

    for idx, step in enumerate(steps):
        print(f"\n>> Step {idx + 1}/{len(steps)}: {step}")

        result = execute_step(
            step_idx=idx,
            steps=steps,
            step_results=step_results,
            memory=memory,
            model=model,
            verbose=verbose,
        )

        if result is None:
            # Agent called finish during this step
            final_answer = step_results[-1] if step_results else "Task completed."
            break

        step_results.append(result)
        print(f"   Result: {result[:300]}")

        memory.append({"role": "assistant", "content": f"Completed step {idx + 1}: {result}"})

    if final_answer is None:
        # All steps done; ask for final synthesis
        print("\n>> Synthesizing final answer...")
        synthesis_prompt = (
            f"All plan steps are done. Here are the results:\n\n"
            + "\n".join(f"Step {i+1}: {r}" for i, r in enumerate(step_results))
            + f"\n\nOriginal task: {task}\n\n"
            "Provide a comprehensive final answer."
        )
        resp = completion(
            model=model,
            messages=[{"role": "user", "content": synthesis_prompt}],
            max_tokens=DEFAULT_MAX_TOKENS,
        )
        final_answer = resp.choices[0].message.content.strip()

    print(f"\n{'=' * 70}")
    print("  TASK COMPLETE")
    print(f"{'=' * 70}")
    print(f"\n{final_answer}\n")
    return final_answer


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Plan-and-Execute Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_planner.py
  python agent_planner.py --task "What does each Python file in this project do?"
  python agent_planner.py --task "Find all TODO comments in the codebase" --verbose

Pattern explained:
  Unlike ReAct (which reasons per-step), this agent creates an explicit plan
  upfront, then executes each step methodically. This works well for tasks
  where you can anticipate the steps ahead of time.
""",
    )
    parser.add_argument("--task", type=str, help="Task for the agent")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key found. Set GEMINI_API_KEY or OPENAI_API_KEY in .env")
        return 1

    if args.task:
        task = args.task
    else:
        print("\nWhat should the planner agent do?")
        task = input("Your task: ").strip()
        if not task:
            print("No task provided.")
            return 1

    try:
        run_planner_agent(task=task, model=args.model, verbose=args.verbose)
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
