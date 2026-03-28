"""
Generator-Critic Agent (Self-Refining)

A two-LLM-persona pattern where:
  Pass 1 (Generator) - Produces an initial output (code, text, plan, etc.)
  Pass 2 (Critic)    - Reviews the output for quality, correctness, gaps
  Pass 3 (Refiner)   - Incorporates the critique to produce an improved version
  ... optionally repeats for N refinement rounds

This is the simplest way to dramatically improve LLM output quality.
The same model plays both roles but with different system prompts.

Usage:
    python agent_critic.py
    python agent_critic.py --task "Write a Python class for a binary search tree"
    python agent_critic.py --task "Write a README for a calculator app" --mode text
    python agent_critic.py --rounds 3 --verbose
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
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from litellm import completion

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))
DEFAULT_ROUNDS = 2


# ---------------------------------------------------------------------------
# System prompts for each persona
# ---------------------------------------------------------------------------

GENERATOR_PROMPTS = {
    "code": (
        "You are an expert Python programmer. Write clean, well-documented, "
        "production-quality code. Include type hints, docstrings, and handle "
        "edge cases. Output ONLY a Python code block."
    ),
    "text": (
        "You are an expert technical writer. Write clear, well-structured "
        "content with proper formatting (headers, lists, examples). "
        "Be thorough but concise."
    ),
    "plan": (
        "You are a senior software architect. Create detailed, actionable "
        "plans with clear steps, dependencies, and considerations. "
        "Include risk assessment and alternatives."
    ),
}

CRITIC_PROMPTS = {
    "code": (
        "You are a meticulous code reviewer. Analyze the code below for:\n"
        "1. CORRECTNESS - Logic errors, off-by-one errors, unhandled edge cases\n"
        "2. QUALITY - Readability, naming, structure, DRY principle\n"
        "3. ROBUSTNESS - Error handling, input validation, type safety\n"
        "4. COMPLETENESS - Missing features, untested scenarios\n"
        "5. PERFORMANCE - Unnecessary complexity, potential bottlenecks\n\n"
        "Rate each category 1-5 and give specific, actionable feedback. "
        "Be strict but constructive."
    ),
    "text": (
        "You are a senior editor. Review the text below for:\n"
        "1. CLARITY - Is it easy to understand? Any ambiguity?\n"
        "2. COMPLETENESS - Any missing information or gaps?\n"
        "3. STRUCTURE - Is the organization logical? Flow?\n"
        "4. ACCURACY - Any factual or technical errors?\n"
        "5. CONCISENESS - Any unnecessary verbosity?\n\n"
        "Rate each category 1-5 and give specific improvement suggestions."
    ),
    "plan": (
        "You are a critical project reviewer. Evaluate the plan below for:\n"
        "1. FEASIBILITY - Can this actually be implemented?\n"
        "2. COMPLETENESS - Any missing steps or considerations?\n"
        "3. ORDERING - Are dependencies and sequence correct?\n"
        "4. RISKS - What could go wrong? Any mitigation?\n"
        "5. CLARITY - Are steps actionable and unambiguous?\n\n"
        "Rate each category 1-5 and provide specific improvements."
    ),
}

REFINER_PROMPT = (
    "You are improving your work based on reviewer feedback. "
    "Address EVERY point raised by the critic. "
    "Produce a complete, improved version (not just the changes). "
    "If the critic's suggestion doesn't apply, briefly explain why."
)


# ---------------------------------------------------------------------------
# Core generate / critique / refine functions
# ---------------------------------------------------------------------------

def llm_call(system: str, user: str, model: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    resp = completion(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def generate(task: str, mode: str, model: str, verbose: bool = False) -> str:
    """Initial generation pass."""
    system = GENERATOR_PROMPTS.get(mode, GENERATOR_PROMPTS["code"])
    result = llm_call(system, task, model)
    if verbose:
        print(f"\n[Generator output]\n{result[:500]}...\n")
    return result


def critique(output: str, task: str, mode: str, model: str, verbose: bool = False) -> str:
    """Critic reviews the output."""
    system = CRITIC_PROMPTS.get(mode, CRITIC_PROMPTS["code"])
    user_msg = f"Original task: {task}\n\nOutput to review:\n\n{output}"
    result = llm_call(system, user_msg, model)
    if verbose:
        print(f"\n[Critic output]\n{result[:500]}...\n")
    return result


def refine(
    original_output: str,
    criticism: str,
    task: str,
    mode: str,
    model: str,
    verbose: bool = False,
) -> str:
    """Refine the output based on criticism."""
    generator_system = GENERATOR_PROMPTS.get(mode, GENERATOR_PROMPTS["code"])
    system = f"{generator_system}\n\n{REFINER_PROMPT}"
    user_msg = (
        f"Original task: {task}\n\n"
        f"Your previous output:\n\n{original_output}\n\n"
        f"Reviewer feedback:\n\n{criticism}\n\n"
        "Please produce an improved complete version addressing all feedback."
    )
    result = llm_call(system, user_msg, model)
    if verbose:
        print(f"\n[Refined output]\n{result[:500]}...\n")
    return result


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_critic_agent(
    task: str,
    mode: str = "code",
    rounds: int = DEFAULT_ROUNDS,
    model: str = DEFAULT_MODEL,
    save_to: Optional[str] = None,
    verbose: bool = False,
) -> Dict:
    """
    Run the generator-critic loop.

    Returns dict with: output, critiques, rounds_completed
    """
    print("\n" + "=" * 70)
    print("  GENERATOR-CRITIC AGENT")
    print("=" * 70)
    print(f"Task  : {task}")
    print(f"Mode  : {mode}")
    print(f"Model : {model}")
    print(f"Rounds: {rounds}\n")

    critiques: List[str] = []

    # Round 0: Initial generation
    print("Round 0: GENERATE")
    print("-" * 40)
    output = generate(task, mode, model, verbose)
    lines = len(output.splitlines())
    print(f"  Generated {lines} lines.\n")

    for r in range(1, rounds + 1):
        # Critique
        print(f"Round {r}/{rounds}: CRITIQUE")
        print("-" * 40)
        criticism = critique(output, task, mode, model, verbose)
        critiques.append(criticism)

        preview = criticism[:400].replace("\n", "\n  ")
        print(f"  {preview}")
        if len(criticism) > 400:
            print(f"  ... ({len(criticism)} chars total)")
        print()

        # Refine
        print(f"Round {r}/{rounds}: REFINE")
        print("-" * 40)
        output = refine(output, criticism, task, mode, model, verbose)
        lines = len(output.splitlines())
        print(f"  Refined to {lines} lines.\n")

    # Final output
    if save_to:
        Path(save_to).write_text(output, encoding="utf-8")
        print(f"Saved to: {save_to}\n")

    print(f"{'=' * 70}")
    print(f"  FINAL OUTPUT ({rounds} critique round(s))")
    print(f"{'=' * 70}")
    print(f"\n{output}\n")

    return {"output": output, "critiques": critiques, "rounds_completed": rounds}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generator-Critic Agent - generates, reviews, and refines output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_critic.py
  python agent_critic.py --task "Write a stack data structure in Python"
  python agent_critic.py --task "Write a README for a todo app" --mode text
  python agent_critic.py --task "Plan a REST API migration" --mode plan
  python agent_critic.py --rounds 3 --verbose
  python agent_critic.py --task "Implement binary search" --save bsearch.py

Modes:
  code  - Generate and review Python code (default)
  text  - Generate and review documentation/text
  plan  - Generate and review project plans

Pattern:
  Generate -> Critique -> Refine -> Critique -> Refine -> ... -> Final Output
  Each round improves quality based on structured feedback.
""",
    )
    parser.add_argument("--task", type=str, help="What to generate")
    parser.add_argument("--mode", choices=["code", "text", "plan"], default="code")
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS, help="Critique-refine rounds")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--save", type=str, help="Save final output to file")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key found. Set GEMINI_API_KEY or OPENAI_API_KEY in .env")
        return 1

    if args.task:
        task = args.task
    else:
        print(f"\nWhat should the agent generate? (mode: {args.mode})")
        print("Example: 'Write a linked list implementation with insert, delete, and search'\n")
        task = input("Your task: ").strip()
        if not task:
            print("No task provided.")
            return 1

    try:
        run_critic_agent(
            task=task,
            mode=args.mode,
            rounds=args.rounds,
            model=args.model,
            save_to=args.save,
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
