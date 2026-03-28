# Self-Healing Code Agent

A code generation agent that writes Python code, executes it in a sandbox, detects failures, and iteratively fixes itself until the code passes.

---

## Architecture

```
User Task
    |
    v
[LLM: Generate Code]
    |
    v
[Execute in Sandbox] ──> Success? ──> YES ──> Done (save code)
    |                                          
    NO (error captured)                        
    |                                          
    v                                          
[LLM: Fix Code] ──────────────────────> (loop back to Execute)
    |
    (max retries exhausted) ──> Report failure
```

## Why This Pattern Matters

LLM-generated code rarely works on the first attempt. Studies show:
- First-pass success rate: ~30-60% depending on complexity
- With self-healing (3-5 retries): ~85-95%

This agent automates the "run, read error, fix, repeat" cycle that humans do manually.

---

## Key Features

- **Subprocess Sandbox**: Code runs in an isolated subprocess, not in the agent's process
- **Timeout Protection**: Infinite loops are killed after 15 seconds
- **Error Feedback Loop**: Full stderr is fed back to the LLM for targeted fixes
- **Code Extraction**: Handles markdown-fenced code blocks from LLM output
- **Save to File**: Working code can be saved directly with `--save`

## Tools

This agent doesn't use the standard tool pattern. Instead, it has two specialized LLM calls:

| Call | System Prompt | Purpose |
|------|--------------|---------|
| `generate_code()` | Expert programmer | Initial code from task description |
| `fix_code()` | Expert debugger | Repair broken code using error output |

And one execution function:

| Function | Input | Output |
|----------|-------|--------|
| `execute_code()` | Python source code | `{success, stdout, stderr, return_code}` |

---

## Prerequisites

1. Python 3.8+
2. Dependencies installed: `pip install -r requirements.txt`
3. API key in `.env`:
   ```
   GEMINI_API_KEY=your-key-here
   ```

## Quick Start

```bash
# Interactive mode
python agent_self_healing.py

# With a specific task
python agent_self_healing.py --task "Write a function that checks if a string is a palindrome"

# More retries for harder tasks
python agent_self_healing.py --task "Implement merge sort" --max-retries 8

# Save the working code
python agent_self_healing.py --task "FizzBuzz from 1 to 100" --save fizzbuzz.py

# See full LLM responses
python agent_self_healing.py --task "Binary search" --verbose
```

## Example Session

```
======================================================================
  SELF-HEALING CODE AGENT
======================================================================
Task   : Write a function that finds all prime numbers up to N using the Sieve of Eratosthenes
Model  : gemini/gemini-1.5-flash
Retries: 5

Step 1: Generating code...
  Generated 25 lines of code.

--- Attempt 1/5 ---
  Executing...
  stderr: Traceback... IndexError: list index out of range
  Failed. Asking LLM to fix...
  Received fixed code (28 lines).

--- Attempt 2/5 ---
  Executing...
  stdout: Primes up to 30: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
          PASS: Found 10 primes up to 30
          PASS: 2 is prime
          PASS: Edge case N=1 returns []

  Code PASSED on attempt 2!
======================================================================
  CODE WORKS!
======================================================================
```

## How It Works

1. **Generate**: The LLM receives a task description and a system prompt that instructs it to produce self-contained Python with test cases and print statements.

2. **Execute**: The generated code is written to a temporary file and run in a subprocess with `sys.executable`. stdout and stderr are captured.

3. **Evaluate**: If return code is 0, the code passed. Otherwise, the error output becomes feedback.

4. **Fix**: The LLM receives the original task, the broken code, and the error output. A different system prompt ("expert debugger") focuses it on root-cause analysis.

5. **Loop**: Steps 2-4 repeat until success or max retries.

## Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `--task` | (interactive) | Code task description |
| `--model` | `gemini/gemini-1.5-flash` | LLM model |
| `--max-retries` | 5 | Max fix attempts |
| `--save` | (none) | Save working code to file |
| `--verbose` | off | Show full LLM responses |

Environment variables:
- `DEFAULT_MODEL` - Override default model
- `DEFAULT_MAX_TOKENS` - Max tokens per LLM call (default: 2048)
- `GEMINI_API_KEY` or `OPENAI_API_KEY` - API authentication

## When to Use This Agent

**Good for:**
- Script generation and automation
- Algorithm implementation
- Data processing pipelines
- Utility function creation

**Not ideal for:**
- Large multi-file projects (use Plan-then-Execute)
- Code that needs human review (use Generator-Critic)
- Code with external dependencies not available in the sandbox

## Cost Estimate

Per task (assuming 2-3 attempts):
- Input tokens: ~2,000-4,000
- Output tokens: ~500-1,500
- Estimated cost: $0.001-0.005 with Gemini Flash

---

## Comparison with Other Agents

| Feature | Self-Healing | ReAct | Critic |
|---------|-------------|-------|--------|
| Validates output | Executes code | No validation | LLM review only |
| Feedback source | Real errors | LLM reasoning | LLM critique |
| Best for | Working code | General tasks | Quality output |
| Iteration trigger | Execution failure | LLM decides | Always iterates |
