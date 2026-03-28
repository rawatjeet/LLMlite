# Generator-Critic Agent

A two-persona pattern where one LLM pass generates output, a second pass critically reviews it, and a third pass refines the output based on the critique. This cycle repeats for N rounds, progressively improving quality.

---

## Architecture

```
User Task
    |
    v
[Generator LLM] ──> Initial Output
    |
    v
┌─────────────────────────────────────┐
│          REFINEMENT ROUND           │
│                                     │
│  [Critic LLM] ──> Structured       │
│      |             Feedback         │
│      v             (1-5 ratings)    │
│  [Refiner LLM] ──> Improved Output │
│                                     │
└─────────────────────────────────────┘
    |           ↑
    |           │ (repeat N rounds)
    |           │
    └───────────┘
    |
    v
Final Output
```

## Why This Pattern Matters

A single LLM generation pass has consistent blind spots. By adding a structured critique step, you get:

- **Catch errors**: The critic persona finds bugs the generator missed
- **Improve quality**: Specific feedback drives targeted improvements
- **Reduce bias**: Two different prompts produce more balanced output
- **No external tools needed**: Works with just LLM calls, no sandbox or retrieval

This is the lowest-effort way to significantly improve LLM output quality.

---

## Key Features

- **Three modes**: Code generation, text writing, and project planning
- **Structured critiques**: 5-category scoring with specific feedback
- **Multiple rounds**: Each round builds on the previous refinement
- **Configurable depth**: 1 round for quick improvement, 3+ for high-stakes output
- **Save to file**: Output can be saved directly

## Modes

| Mode | Generator Persona | Critic Persona | Best For |
|------|------------------|----------------|----------|
| `code` | Expert Python programmer | Meticulous code reviewer | Functions, classes, scripts |
| `text` | Technical writer | Senior editor | READMEs, docs, articles |
| `plan` | Software architect | Project reviewer | Roadmaps, designs, migrations |

## Critique Categories

### Code Mode
1. **Correctness** - Logic errors, edge cases
2. **Quality** - Readability, naming, structure
3. **Robustness** - Error handling, type safety
4. **Completeness** - Missing features, scenarios
5. **Performance** - Complexity, bottlenecks

### Text Mode
1. **Clarity** - Easy to understand?
2. **Completeness** - Any gaps?
3. **Structure** - Logical organization?
4. **Accuracy** - Factual correctness?
5. **Conciseness** - Unnecessary verbosity?

### Plan Mode
1. **Feasibility** - Can it be done?
2. **Completeness** - Missing steps?
3. **Ordering** - Correct sequence?
4. **Risks** - What could go wrong?
5. **Clarity** - Are steps actionable?

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
python agent_critic.py

# Generate and refine code
python agent_critic.py --task "Write a Python class for a binary search tree"

# Generate and refine documentation
python agent_critic.py --task "Write a README for a calculator app" --mode text

# Generate and refine a plan
python agent_critic.py --task "Plan a REST API migration" --mode plan

# More refinement rounds for critical output
python agent_critic.py --task "Implement a thread pool" --rounds 3

# Save final output
python agent_critic.py --task "Write a linked list" --save linked_list.py

# See all LLM responses
python agent_critic.py --verbose
```

## Example Session

```
======================================================================
  GENERATOR-CRITIC AGENT
======================================================================
Task  : Write a Python class for a stack with push, pop, peek, and is_empty
Mode  : code
Model : gemini/gemini-1.5-flash
Rounds: 2

Round 0: GENERATE
----------------------------------------
  Generated 35 lines.

Round 1/2: CRITIQUE
----------------------------------------
  CORRECTNESS: 4/5 - Logic is sound but pop() doesn't handle empty stack
  QUALITY: 3/5 - Missing type hints and docstrings
  ROBUSTNESS: 2/5 - No error handling for pop/peek on empty stack
  COMPLETENESS: 3/5 - Missing __len__, __repr__, and iteration support
  PERFORMANCE: 5/5 - O(1) operations using list

Round 1/2: REFINE
----------------------------------------
  Refined to 52 lines.

Round 2/2: CRITIQUE
----------------------------------------
  CORRECTNESS: 5/5 - All operations handle edge cases correctly
  QUALITY: 5/5 - Clean code with type hints and docstrings
  ROBUSTNESS: 5/5 - Proper error handling with custom exceptions
  COMPLETENESS: 4/5 - Could add from_iterable() class method
  PERFORMANCE: 5/5 - Optimal implementation

Round 2/2: REFINE
----------------------------------------
  Refined to 58 lines.

======================================================================
  FINAL OUTPUT (2 critique round(s))
======================================================================

class StackError(Exception):
    """Custom exception for stack operations."""
    pass

class Stack:
    """A stack (LIFO) data structure with full error handling."""
    ...
```

## How It Works

### Round 0: Generation

The generator receives the task and produces initial output. The system prompt varies by mode:
- **Code mode**: "Write clean, production-quality Python code"
- **Text mode**: "Write clear, well-structured content"
- **Plan mode**: "Create detailed, actionable plans"

### Round N: Critique

The critic receives the original task AND the current output. It evaluates 5 categories, rates each 1-5, and provides specific actionable feedback.

The critic prompt is designed to be **strict but constructive** - it always suggests how to fix issues, not just identifies them.

### Round N: Refine

The refiner receives:
1. The original task
2. The current output
3. The critic's feedback

It produces a **complete improved version** (not a diff), addressing every point raised.

## Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `--task` | (interactive) | What to generate |
| `--mode` | `code` | `code`, `text`, or `plan` |
| `--rounds` | 2 | Critique-refine rounds |
| `--model` | `gemini/gemini-1.5-flash` | LLM model |
| `--save` | (none) | Save final output to file |
| `--verbose` | off | Show full LLM responses |

Environment variables:
- `DEFAULT_MODEL` - Override default model
- `DEFAULT_MAX_TOKENS` - Max tokens per LLM call (default: 2048)
- `GEMINI_API_KEY` or `OPENAI_API_KEY` - API authentication

### How Many Rounds?

| Rounds | Use Case | Cost Multiplier |
|--------|----------|----------------|
| 1 | Quick improvement, prototyping | 3x (generate + critique + refine) |
| 2 | Standard quality (recommended) | 5x |
| 3 | High-stakes output | 7x |
| 4+ | Diminishing returns for most tasks | 9x+ |

## When to Use This Agent

**Good for:**
- Writing production code that needs to be high quality
- Creating documentation, READMEs, guides
- Project planning and architecture design
- Any task where "good enough on first try" isn't enough

**Not ideal for:**
- Tasks needing real execution validation (use Self-Healing)
- Simple tasks where first-pass output is adequate
- Real-time/interactive use (multiple LLM calls add latency)

## Cost Estimate

Per task (2 rounds):
- LLM calls: 5 (generate + 2x critique + 2x refine)
- Input tokens: ~3,000-8,000 total
- Output tokens: ~2,000-5,000 total
- Estimated cost: $0.003-0.010 with Gemini Flash

---

## Comparison with Other Agents

| Feature | Critic | Self-Healing | ReAct |
|---------|--------|-------------|-------|
| Validation | LLM review | Code execution | None |
| Always iterates | Yes (N rounds) | Only on failure | LLM decides |
| Output quality | Highest | Code correctness | Variable |
| Modes | code/text/plan | Code only | General |
| Cost | Higher (N*2+1 calls) | Lower (1-5 calls) | Variable |

## Possible Enhancements

- Add a "consensus" mode where multiple generators produce candidates and the critic picks the best
- Implement critique history: later rounds see all previous critiques
- Add domain-specific critic prompts (security review, accessibility review, etc.)
- Score tracking: plot improvement across rounds
