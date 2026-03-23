"""
Multi-Agent Orchestrator

Implements the delegation pattern where a "Router" agent analyzes the user
request and delegates work to specialized sub-agents:

  Router Agent (orchestrator)
    |-- Code Analyst Agent    (reads and analyzes code files)
    |-- Writer Agent          (creates documentation and text content)
    |-- Researcher Agent      (searches files and gathers information)

Each sub-agent has its own system prompt and tool set. The router decides
which specialist to call and synthesizes the final answer.

This demonstrates how to compose multiple agents into a larger system.

Usage:
    python agent_multi.py
    python agent_multi.py --task "Analyze the project and write a summary"
    python agent_multi.py --verbose
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
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from litellm import completion

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))


# ---------------------------------------------------------------------------
# Shared tools
# ---------------------------------------------------------------------------

def list_files(directory: str = ".") -> str:
    try:
        items = sorted(i.name + ("/" if i.is_dir() else "") for i in Path(directory).iterdir())
        return "\n".join(items) if items else "(empty)"
    except Exception as e:
        return f"Error: {e}"


def read_file(file_name: str) -> str:
    try:
        p = Path(file_name)
        if not p.is_file():
            return f"Error: '{file_name}' not found."
        content = p.read_text(encoding="utf-8")
        if len(content) > 30_000:
            return content[:30_000] + f"\n... (truncated, {len(content)} chars total)"
        return content
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
        matches = sorted(str(p) for p in Path(directory).rglob(pattern) if p.is_file())
        return "\n".join(matches[:50]) if matches else "No matches."
    except Exception as e:
        return f"Error: {e}"


TOOL_FUNCTIONS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "search_files": search_files,
}

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files/directories at a path.",
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
            "description": "Read text content of a file.",
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
            "name": "write_file",
            "description": "Write text to a file.",
            "parameters": {
                "type": "object",
                "properties": {"file_name": {"type": "string"}, "content": {"type": "string"}},
                "required": ["file_name", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Recursively search for files matching a glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {"pattern": {"type": "string"}, "directory": {"type": "string"}},
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "done",
            "description": "Signal that this sub-agent is finished and return the result.",
            "parameters": {
                "type": "object",
                "properties": {"result": {"type": "string", "description": "The output/findings to return"}},
                "required": ["result"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Sub-agent definitions
# ---------------------------------------------------------------------------

AGENTS = {
    "code_analyst": {
        "name": "Code Analyst",
        "system_prompt": (
            "You are a code analyst agent. Your job is to read source code files "
            "and provide detailed analysis: what each file does, key functions/classes, "
            "dependencies, and architecture patterns.\n\n"
            "Use the tools to explore the codebase. When you have enough information, "
            "call the 'done' tool with your analysis."
        ),
        "tools": ["list_files", "read_file", "search_files", "done"],
    },
    "writer": {
        "name": "Writer",
        "system_prompt": (
            "You are a technical writer agent. Your job is to create clear, "
            "well-structured documentation, summaries, README files, or other text content.\n\n"
            "You may use tools to read existing files for context. When your writing "
            "is ready, call the 'done' tool with the content. If asked to write to a "
            "file, use write_file first, then call done."
        ),
        "tools": ["list_files", "read_file", "write_file", "done"],
    },
    "researcher": {
        "name": "Researcher",
        "system_prompt": (
            "You are a research agent. Your job is to search through files, "
            "find specific information, patterns, or data. You are thorough and "
            "systematic.\n\n"
            "Use search_files to find relevant files, then read_file to examine them. "
            "When you have gathered all needed information, call 'done' with your findings."
        ),
        "tools": ["list_files", "read_file", "search_files", "done"],
    },
}


# ---------------------------------------------------------------------------
# Sub-agent runner
# ---------------------------------------------------------------------------

def run_sub_agent(
    agent_key: str,
    task: str,
    model: str = DEFAULT_MODEL,
    verbose: bool = False,
    max_tool_calls: int = 15,
) -> str:
    """Run a specialized sub-agent and return its result."""
    agent_def = AGENTS[agent_key]
    agent_name = agent_def["name"]

    print(f"\n  [{agent_name}] Starting: {task[:100]}")

    allowed_tools = [t for t in TOOLS_SPEC if t["function"]["name"] in agent_def["tools"]]

    messages = [
        {"role": "system", "content": agent_def["system_prompt"]},
        {"role": "user", "content": task},
    ]

    for call_num in range(max_tool_calls):
        resp = completion(model=model, messages=messages, tools=allowed_tools, max_tokens=DEFAULT_MAX_TOKENS)
        msg = resp.choices[0].message

        if not msg.tool_calls:
            text = msg.content or ""
            if verbose:
                print(f"  [{agent_name}] Text: {text[:200]}")
            return text.strip()

        tool_call = msg.tool_calls[0]
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)

        if fn_name == "done":
            result = fn_args.get("result", "")
            print(f"  [{agent_name}] Done ({len(result)} chars)")
            return result

        if verbose:
            print(f"  [{agent_name}] Tool: {fn_name}({fn_args})")

        if fn_name in TOOL_FUNCTIONS:
            try:
                tool_result = TOOL_FUNCTIONS[fn_name](**fn_args)
            except Exception as e:
                tool_result = f"Error: {e}"
        else:
            tool_result = f"Unknown tool: {fn_name}"

        action_json = json.dumps({"tool": fn_name, "args": fn_args})
        messages.append({"role": "assistant", "content": action_json})
        messages.append({"role": "user", "content": f"Tool result:\n{tool_result}"})

    return f"[{agent_name}] Reached max tool calls without finishing."


# ---------------------------------------------------------------------------
# Router agent
# ---------------------------------------------------------------------------

ROUTER_SYSTEM_PROMPT = """You are a router agent that delegates tasks to specialist agents.

Available specialists:
- code_analyst: Reads and analyzes source code files. Use for understanding code.
- writer: Creates documentation, summaries, or text content. Use for writing tasks.
- researcher: Searches files and gathers specific information. Use for finding things.

You must respond with a JSON array of delegation steps. Each step is an object with:
  "agent": the specialist to use (code_analyst, writer, or researcher)
  "task": what the specialist should do (be specific and detailed)

You can call the same specialist multiple times if needed.
After all specialists complete, you'll synthesize their results.

Output ONLY the JSON array, no extra commentary.

Example:
[
  {"agent": "researcher", "task": "Find all Python files and list them"},
  {"agent": "code_analyst", "task": "Analyze the main entry point files"},
  {"agent": "writer", "task": "Write a project summary based on the analysis"}
]
"""


def route_task(task: str, model: str, verbose: bool = False) -> List[Dict]:
    """Ask the router to create a delegation plan."""
    resp = completion(
        model=model,
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ],
        max_tokens=1024,
    )
    raw = resp.choices[0].message.content.strip()

    if verbose:
        print(f"[Router raw]\n{raw}\n")

    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        plan = json.loads(raw)
        if isinstance(plan, list):
            return plan
    except json.JSONDecodeError:
        pass

    return [{"agent": "code_analyst", "task": task}]


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_multi_agent(
    task: str,
    model: str = DEFAULT_MODEL,
    verbose: bool = False,
) -> str:
    print("\n" + "=" * 70)
    print("  MULTI-AGENT ORCHESTRATOR")
    print("=" * 70)
    print(f"Task : {task}")
    print(f"Model: {model}\n")

    # Phase 1: Route
    print("Phase 1: ROUTING")
    print("-" * 40)
    delegation_plan = route_task(task, model, verbose)

    for i, step in enumerate(delegation_plan):
        agent = step.get("agent", "unknown")
        sub_task = step.get("task", "")
        agent_display = AGENTS.get(agent, {}).get("name", agent)
        print(f"  {i + 1}. [{agent_display}] {sub_task[:80]}")
    print()

    # Phase 2: Execute delegations
    print("Phase 2: DELEGATION")
    print("-" * 40)

    results = []
    for i, step in enumerate(delegation_plan):
        agent_key = step.get("agent", "code_analyst")
        sub_task = step.get("task", task)

        if agent_key not in AGENTS:
            print(f"  Warning: Unknown agent '{agent_key}', using code_analyst.")
            agent_key = "code_analyst"

        # Pass previous results as context to later agents
        context = ""
        if results:
            context = "\n\nContext from previous steps:\n"
            for j, r in enumerate(results):
                context += f"\n--- Step {j + 1} result ---\n{r[:2000]}\n"

        full_task = sub_task + context

        result = run_sub_agent(agent_key, full_task, model, verbose)
        results.append(result)

    # Phase 3: Synthesize
    print(f"\nPhase 3: SYNTHESIS")
    print("-" * 40)

    synthesis_prompt = f"""Original task: {task}

Results from specialist agents:

"""
    for i, r in enumerate(results):
        agent_key = delegation_plan[i].get("agent", "unknown")
        agent_name = AGENTS.get(agent_key, {}).get("name", agent_key)
        synthesis_prompt += f"\n--- {agent_name} ---\n{r}\n"

    synthesis_prompt += "\nPlease synthesize these results into a comprehensive final answer."

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
        description="Multi-Agent Orchestrator - Router + Specialist Agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_multi.py
  python agent_multi.py --task "Analyze this project and write documentation"
  python agent_multi.py --task "Find all functions across the codebase" --verbose

Architecture:
  Router Agent decides how to split the work among specialists:
    - Code Analyst: reads and understands source code
    - Writer: creates documentation and summaries
    - Researcher: searches for files and specific information
""",
    )
    parser.add_argument("--task", type=str, help="Task for the multi-agent system")
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
        print("\nWhat should the multi-agent system do?")
        task = input("Your task: ").strip()
        if not task:
            print("No task provided.")
            return 1

    try:
        run_multi_agent(task=task, model=args.model, verbose=args.verbose)
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
