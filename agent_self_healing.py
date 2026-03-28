"""
Self-Healing Code Agent

Generates Python code from a natural language description, then executes it
in a sandbox. If the code fails (syntax error, runtime exception, wrong output),
the agent feeds the error back to the LLM and asks it to fix the code.
This loop repeats until the code passes or max retries are exhausted.

This is the most practical pattern for automated code generation because
real-world LLM output almost never works on the first try.

Pattern:
    describe task → generate code → execute → if error → feed error back → regenerate → ...

Usage:
    python agent_self_healing.py
    python agent_self_healing.py --task "Write a function that checks if a string is a palindrome"
    python agent_self_healing.py --task "Sort a list of dicts by the 'age' key" --max-retries 5
    python agent_self_healing.py --verbose
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
import sys
import json
import argparse
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from litellm import completion

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))
DEFAULT_MAX_RETRIES = 5


# ---------------------------------------------------------------------------
# Code extraction
# ---------------------------------------------------------------------------

def extract_python_code(response: str) -> str:
    """Extract Python code from a markdown-fenced LLM response."""
    if "```python" in response:
        blocks = re.findall(r"```python\s*\n(.*?)```", response, re.DOTALL)
        if blocks:
            return blocks[0].strip()

    if "```" in response:
        blocks = re.findall(r"```\s*\n(.*?)```", response, re.DOTALL)
        if blocks:
            return blocks[0].strip()

    return response.strip()


# ---------------------------------------------------------------------------
# Sandbox execution
# ---------------------------------------------------------------------------

def execute_code(code: str, timeout: int = 15) -> Dict:
    """
    Execute Python code in a subprocess sandbox.

    Returns dict with:
        success: bool
        stdout: str
        stderr: str
        return_code: int
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir(),
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "return_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"TIMEOUT: Code did not finish within {timeout} seconds.",
            "return_code": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"EXECUTION ERROR: {e}",
            "return_code": -1,
        }
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# LLM prompts
# ---------------------------------------------------------------------------

GENERATE_SYSTEM = """You are an expert Python programmer. Generate clean, working Python code.

Rules:
1. Output ONLY a Python code block (```python ... ```)
2. The code must be self-contained and runnable as a standalone script
3. Include a few print() statements to demonstrate the code works
4. Include basic test cases that print PASS/FAIL
5. Do NOT use input() or any interactive elements
6. Handle edge cases properly
"""

FIX_SYSTEM = """You are an expert Python debugger. The code below failed when executed.
Analyze the error, fix the code, and return a corrected version.

Rules:
1. Output ONLY a corrected Python code block (```python ... ```)
2. Fix the root cause, not just the symptom
3. Keep the same functionality as intended
4. The code must be self-contained and runnable
5. Include print() statements to verify it works
"""


def generate_code(task: str, model: str, verbose: bool = False) -> str:
    """Ask the LLM to generate code for a task."""
    resp = completion(
        model=model,
        messages=[
            {"role": "system", "content": GENERATE_SYSTEM},
            {"role": "user", "content": f"Write Python code that: {task}"},
        ],
        max_tokens=DEFAULT_MAX_TOKENS,
    )
    raw = resp.choices[0].message.content.strip()
    if verbose:
        print(f"\n[LLM raw response]\n{raw}\n")
    return extract_python_code(raw)


def fix_code(
    task: str,
    broken_code: str,
    error: str,
    attempt: int,
    model: str,
    verbose: bool = False,
) -> str:
    """Ask the LLM to fix code that failed."""
    user_msg = (
        f"Original task: {task}\n\n"
        f"Attempt {attempt} code:\n```python\n{broken_code}\n```\n\n"
        f"Error output:\n```\n{error}\n```\n\n"
        "Please fix the code and return a working version."
    )
    resp = completion(
        model=model,
        messages=[
            {"role": "system", "content": FIX_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=DEFAULT_MAX_TOKENS,
    )
    raw = resp.choices[0].message.content.strip()
    if verbose:
        print(f"\n[Fix response]\n{raw}\n")
    return extract_python_code(raw)


# ---------------------------------------------------------------------------
# Main self-healing loop
# ---------------------------------------------------------------------------

def run_self_healing(
    task: str,
    model: str = DEFAULT_MODEL,
    max_retries: int = DEFAULT_MAX_RETRIES,
    save_to: Optional[str] = None,
    verbose: bool = False,
) -> Dict:
    """
    Generate code, execute it, and fix it until it works.

    Returns dict with: success, code, attempts, history
    """
    print("\n" + "=" * 70)
    print("  SELF-HEALING CODE AGENT")
    print("=" * 70)
    print(f"Task   : {task}")
    print(f"Model  : {model}")
    print(f"Retries: {max_retries}\n")

    history: List[Dict] = []

    # Step 1: Initial generation
    print("Step 1: Generating code...")
    code = generate_code(task, model, verbose)
    print(f"  Generated {len(code.splitlines())} lines of code.")

    for attempt in range(1, max_retries + 1):
        print(f"\n--- Attempt {attempt}/{max_retries} ---")

        # Step 2: Execute
        print("  Executing...")
        result = execute_code(code)

        history.append({
            "attempt": attempt,
            "code": code,
            "success": result["success"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
        })

        if result["stdout"]:
            print(f"  stdout: {result['stdout'][:300]}")
        if result["stderr"]:
            print(f"  stderr: {result['stderr'][:300]}")

        # Step 3: Check success
        if result["success"]:
            print(f"\n  Code PASSED on attempt {attempt}!")

            if save_to:
                Path(save_to).write_text(code, encoding="utf-8")
                print(f"  Saved to: {save_to}")

            print(f"\n{'=' * 70}")
            print("  CODE WORKS!")
            print(f"{'=' * 70}")
            print(f"\n{code}\n")
            return {"success": True, "code": code, "attempts": attempt, "history": history}

        # Step 4: Fix
        if attempt < max_retries:
            error_context = result["stderr"] or result["stdout"] or "Code returned non-zero exit code"
            print(f"  Failed. Asking LLM to fix...")
            code = fix_code(task, code, error_context, attempt, model, verbose)
            print(f"  Received fixed code ({len(code.splitlines())} lines).")

    print(f"\n{'=' * 70}")
    print(f"  FAILED after {max_retries} attempts")
    print(f"{'=' * 70}")
    return {"success": False, "code": code, "attempts": max_retries, "history": history}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Self-Healing Code Agent - generates, tests, and fixes code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_self_healing.py
  python agent_self_healing.py --task "Check if a number is prime"
  python agent_self_healing.py --task "Merge two sorted lists" --max-retries 5
  python agent_self_healing.py --task "FizzBuzz from 1 to 30" --save output.py
  python agent_self_healing.py --verbose

Pattern:
  Generate code -> Execute -> If error, feed back to LLM -> Fix -> Repeat
  This is how production code-generation systems actually work.
""",
    )
    parser.add_argument("--task", type=str, help="What code to generate")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--save", type=str, help="Save working code to this file")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key found. Set GEMINI_API_KEY or OPENAI_API_KEY in .env")
        return 1

    if args.task:
        task = args.task
    else:
        print("\nDescribe the code you want the agent to generate:")
        print("Example: 'A function that finds the longest common subsequence of two strings'\n")
        task = input("Your task: ").strip()
        if not task:
            print("No task provided.")
            return 1

    try:
        result = run_self_healing(
            task=task,
            model=args.model,
            max_retries=args.max_retries,
            save_to=args.save,
            verbose=args.verbose,
        )
        return 0 if result["success"] else 1
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
