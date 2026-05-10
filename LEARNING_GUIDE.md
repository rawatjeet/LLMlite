# LLMlite — Beginner's Learning Guide

Welcome! This guide is your **gentle, hand-held walkthrough** of the entire LLMlite project. No prior experience with AI agents is required. We will start from "what is an LLM?" and end with "how do I build my own agent?"

> If you have never written Python before, you can still read this guide cover-to-cover. But you should learn the basics of Python first (variables, functions, dictionaries, loops) before running the code.

---

## Table of Contents

1. [Before You Begin: 5 Concepts in Plain English](#1-before-you-begin-5-concepts-in-plain-english)
2. [Setting Up the Project](#2-setting-up-the-project)
3. [The Big Picture: What Each File Does](#3-the-big-picture-what-each-file-does)
4. [The 8 Learning Levels — Step by Step](#4-the-8-learning-levels--step-by-step)
5. [Glossary](#5-glossary)
6. [How to Read Any Script in This Repo](#6-how-to-read-any-script-in-this-repo)
7. [Your First "Hello, Agent!" Exercise](#7-your-first-hello-agent-exercise)
8. [Common Mistakes Beginners Make](#8-common-mistakes-beginners-make)
9. [Where to Go Next](#9-where-to-go-next)

---

## 1. Before You Begin: 5 Concepts in Plain English

If you're new to AI development, just learn these five words. The rest of the project is built on top of them.

### 1.1 LLM (Large Language Model)
A program that has read most of the internet and learned to predict the next word in a sentence. Examples: GPT-4, Gemini, Claude. You give it some text, it gives you back text.

```
You: "The capital of France is"
LLM: " Paris."
```

That's literally all an LLM does. Everything else — chat, agents, function calling — is just clever ways of feeding text in and getting useful text back out.

### 1.2 API (Application Programming Interface)
A doorway that lets your code talk to someone else's service. Instead of opening ChatGPT in a browser, your Python script sends a request to OpenAI's servers and gets the model's answer back as data.

```python
response = completion(model="gpt-4", messages=[...])
print(response.choices[0].message.content)
```

### 1.3 API Key
A long secret password that proves *you* are the one calling the API. You get one from the provider's website (e.g., [makersuite.google.com](https://makersuite.google.com/app/apikey) for Gemini — free).

> **Rule #1:** never put an API key directly in your code. Put it in a `.env` file (this project does that automatically).

### 1.4 Prompt
The text you send to the LLM. There are usually three "roles":

| Role | Who is it? | Example |
|------|-----------|---------|
| `system` | Instructions for the assistant | "You are a helpful Python tutor." |
| `user` | What the user is asking | "Explain decorators." |
| `assistant` | What the LLM said back | "A decorator is a function that..." |

Most agents send a `system` message + one or more `user` messages and get an `assistant` reply.

### 1.5 Agent
**An LLM stuck in a loop, with the ability to use tools.**

That's it. That's the whole field. Everything in this project is just variations on:

```
while not done:
    1. Ask the LLM what to do
    2. Do it (call a function, read a file, search, etc.)
    3. Tell the LLM what happened
    4. Go back to step 1
```

---

## 2. Setting Up the Project

You need this once.

### Step 1 — Install Python 3.8 or newer
Type `python --version` in your terminal. If it says 3.8 or higher, you're good.

### Step 2 — Create a virtual environment
A virtual environment is a private "sandbox" so this project's dependencies don't mix with other projects on your computer.

```powershell
# Windows PowerShell
python -m venv .venv
.venv\Scripts\activate
```

```bash
# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

This installs:
- **`litellm`** — the magic library that makes your code work with *any* LLM provider (OpenAI, Gemini, Anthropic, …) using the same calls.
- **`python-dotenv`** — reads your `.env` file and turns each line into an environment variable.

### Step 4 — Get an API key (free)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey).
2. Sign in, click "Create API key", copy it.
3. Create a file called `.env` in this folder with this content:

```env
GEMINI_API_KEY=paste-your-key-here
DEFAULT_MODEL=gemini/gemini-1.5-flash
```

> The `DEFAULT_MODEL` line tells every script to use the free Gemini model unless you override it.

### Step 5 — Verify the setup works
```bash
python main_improved.py --mock
```

If you see a "Hello!" mock response, congrats — you're ready to learn agents.

---

## 3. The Big Picture: What Each File Does

The repo has many files. Don't be intimidated — they fall into three buckets:

| Bucket | What it is | How to treat it |
|--------|-----------|-----------------|
| **Learning scripts** (`main.py`, `quasi-agent.py`, `agent_*.py`, …) | The 8 levels of AI patterns | **Read these in order.** This guide tells you which. |
| **Generated files** (`factorial.py`, `regular_expression_matching.py`, …) | Output produced by `quasi-agent.py` runs | Just example outputs; ignore unless curious. |
| **Documentation** (`README.md`, `*_readme.md`, this file) | Explanations | Read alongside the script you're studying. |

### Naming convention you'll see everywhere
- `something.py` → original, simple version (the *teaching* version).
- `something_improved.py` → cleaned-up, production-style version (the *real* version).
- `something_readme.md` → companion document explaining how `something.py` works.

The pair `original + improved` exists so you can see **the same idea written two ways** — first to learn, then to ship.

---

## 4. The 8 Learning Levels — Step by Step

Each level introduces **exactly one new concept**. Don't skip ahead — each level relies on the one before it.

```
┌────────────────────────────────────────────────────────────┐
│ Level 1   Just call an LLM                                  │
│ Level 2   Call it three times in a row                      │
│ Level 3   Let the LLM call your Python functions            │
│ Level 4   Put step 3 in a loop                              │
│ Level 5   Wrap it in a real architecture                    │
│ Level 6   Make the LLM explain its thinking + plan          │
│ Level 7   Make it remember & let multiple agents collaborate│
│ Level 8   Specialized agents (self-fixing, RAG, critic)     │
└────────────────────────────────────────────────────────────┘
```

### Level 1 — Just Call the LLM

**File:** `main.py` (basic) → `main_improved.py` (clean version)

This script does *one* thing: it sends "Say hello" to the LLM and prints the answer. That's it.

```python
messages = [{"role": "user", "content": "Say hello"}]
response = completion(model="gpt-3.5-turbo", messages=messages)
print(response.choices[0].message.content)
```

Mental model:

```
   Your script  ──[messages]──▶  LLM API  ──[answer]──▶  Your script
                                                          │
                                                       prints it
```

**Run it:**
```bash
python main_improved.py --mock          # no API call, free
python main_improved.py                 # real API call
```

**What's new at this level:**
- How to send messages to an LLM.
- How to handle "rate limit" errors with retry + backoff (waiting longer each time).

---

### Level 2 — A Workflow (Multiple Calls in a Row)

**File:** `quasi-agent.py` → `quasi_agent_improved.py`

A "quasi-agent" is **not yet a real agent** — it's just a script that calls the LLM three times in a fixed order:

```
Step 1: "Write a function that does X"
Step 2: "Add documentation to that function"
Step 3: "Add unit tests to that function"
```

The output of step 1 is fed into step 2, and so on.

```
[Idea]
   │
   ▼
[Generate code]  ─▶  [Add docs]  ─▶  [Add tests]  ─▶  [Save to .py]
```

**Run it:**
```bash
python quasi_agent_improved.py
# It will ask: "What kind of function would you like?"
# Try: "calculates the factorial of a number"
```

**What's new at this level:**
- **Conversation memory**: each call remembers what the previous one said.
- **Caching**: if you ask the same thing twice, it reads from a `.llm_cache/` folder instead of paying for the API again.

The downside: this script can only do *exactly* the steps the programmer hardcoded. It cannot decide, "wait, I should research this first." That's why we need real agents.

---

### Level 3 — Function Calling (Letting the LLM Use Your Code)

**Files (in order):**
1. `llm_function_call.py` → single tool call, no loop
2. `agent_tools.py` → loop with custom JSON parsing
3. `agent_tools_improved.py` → cleaned up version

This is the magic moment. You give the LLM a list of Python functions, and it picks one and tells you which arguments to pass.

```
You: "What files are in this directory?"
LLM: "I'll call list_files()"
You (script): runs list_files() → ['README.md', 'main.py', ...]
You: "Now what?"
LLM: "Done — here are the files."
```

The list of functions is given to the LLM in this format:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Returns a list of files in the directory.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]
```

**`agent_tools.py` vs `llm_function_call.py`:**
- `llm_function_call.py` does **one** call.
- `agent_tools.py` puts it in a **loop** — the LLM can call function after function until it says "I'm done."

**Run it:**
```bash
python agent_tools_improved.py --task "List all Python files and tell me what each one does"
```

**What's new at this level:**
- Tool definitions (a JSON schema describing what each function does).
- The loop pattern (think → call → observe → think again).

---

### Level 4 — Native Function Calling

**Files:**
- `agent_loop_with_function_calling.py` → simple version
- `agent_loop_with_function_calling_improved.py` → polished
- `agent_loop_with_function_calling2.py` → adds batch operations
- `agent_loop_with_function_calling2_improved.py` → polished batch

Modern LLMs (GPT-4, Gemini) have **native** function calling — instead of you parsing weird JSON out of their text, they return a structured `tool_calls` field directly.

The difference looks like this:

```python
# OLD WAY (Level 3): you parse the response yourself
response_text = "I will call ```action {...}```"
parsed = parse_with_regex(response_text)   # painful

# NEW WAY (Level 4): the LLM gives you structured data
response.choices[0].message.tool_calls[0].function.name   # 'list_files'
response.choices[0].message.tool_calls[0].function.arguments  # '{}'
```

That's a small change in code but a **huge** quality of life improvement.

**Run it:**
```bash
python agent_loop_with_function_calling_improved.py --task "Read the README and summarize it"
```

The `..2.py` variants add a `read_all_files()` tool that reads many files at once. This is faster and cheaper than calling `read_file()` 20 times.

**What's new at this level:**
- Native `tool_calls` (no manual parsing).
- Batch operations (one call, many results).

---

### Level 5 — A Real Architecture (the GAME Framework)

**Files:**
- `a_sample_agent_framework.py` → basic GAME architecture
- `a_sample_agent_framework_improved.py` → polished
- `tool_decorators.py` → `@register_tool` decorator pattern

So far, our agents have been ad-hoc scripts. Real agents need **structure**. The GAME framework breaks an agent into 4 named parts:

| Letter | Means | What it stores |
|--------|-------|----------------|
| **G** | **Goal** | "What is the agent trying to do?" |
| **A** | **Actions** | "What can it do?" (the tools) |
| **M** | **Memory** | "What has happened so far?" (the message history) |
| **E** | **Environment** | "What can it see/touch?" (the file system, APIs, etc.) |

Diagram:

```
       Goal
        │
        ▼
    ┌────────┐
    │  LLM   │ ◀──── Memory (chat history)
    └────────┘
        │
        ▼
    Pick an Action
        │
        ▼
   Run it on the Environment
        │
        ▼
   Result goes into Memory
        │
        └─── loop back ───┐
                          ▼
                    (until Goal is met)
```

**`tool_decorators.py`** is a separate, very useful idea: instead of writing tool definitions by hand, you decorate a Python function and the schema is generated automatically:

```python
@register_tool(tags=["files"])
def read_file(path: str) -> str:
    """Read a file from disk."""
    return Path(path).read_text()

# Now the LLM can use read_file with no extra config.
```

**Run it:**
```bash
python a_sample_agent_framework_improved.py --task "Analyze each Python file" --verbose
python tool_decorators.py                  # built-in demo
```

**What's new at this level:**
- Goals as a named concept.
- Memory as a class, not a list.
- Decorator-based tool registration.

---

### Level 6 — Smarter Reasoning (ReAct & Plan-and-Execute)

By now, the agent works but it's a bit **dumb** — it doesn't explain *why* it picked an action, and it doesn't think ahead. Two patterns fix that.

#### 6a. ReAct — "Reason, then Act"
**File:** `agent_react.py`

The LLM is forced to write its reasoning *before* every action:

```
Thought: I need to find Python files first.
Action: list_files()
Observation: ['README.md', 'main.py', 'agent_react.py', ...]

Thought: I'll read main.py to understand what it does.
Action: read_file("main.py")
Observation: <contents of main.py>

Thought: Now I have enough info.
Action: finish("This project teaches AI agents...")
```

This **drastically** improves decision quality on multi-step tasks. The LLM literally talks itself through the problem.

**Run it:**
```bash
python agent_react.py --task "What does this project do?" --verbose
```

#### 6b. Plan-and-Execute
**File:** `agent_planner.py`

Instead of deciding one step at a time, the LLM writes a *full plan* upfront, then executes each step in order:

```
Plan:
  1. List Python files                          [TODO]
  2. Read each file                             [TODO]
  3. Identify functions in each file            [TODO]
  4. Summarize the overall architecture         [TODO]

Executing step 1...  →  [DONE]
Executing step 2...  →  [DONE]
...
```

The agent tracks `[DONE]/[TODO]` markers so it never loses track.

**Run it:**
```bash
python agent_planner.py --task "Analyze the project and list every function"
```

**What's new at this level:**
- Forcing the LLM to **show its reasoning** (ReAct).
- Forcing it to **commit to a plan** (Plan-and-Execute).

---

### Level 7 — Production Patterns

Real assistants need to remember conversations and split work across specialists.

#### 7a. Conversational Agent (Persistent Chat)
**File:** `agent_conversational.py`

This is a **REPL** (Read-Eval-Print Loop) — you can keep talking to it like ChatGPT, and it saves your conversation to disk so you can resume later.

```bash
python agent_conversational.py                  # start a new chat
python agent_conversational.py --resume latest  # continue last chat
python agent_conversational.py --list-sessions  # show saved chats
```

Sessions are saved as JSON in `.agent_sessions/`. Each session has a unique ID.

#### 7b. Multi-Agent Orchestrator
**File:** `agent_multi.py`

Instead of one big agent that does everything, this script has:

```
            ┌──────────────────┐
            │   Router Agent   │
            │  (the manager)   │
            └────────┬─────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌────────────┐
   │  Code   │  │ Writer  │  │ Researcher │
   │ Analyst │  │  Agent  │  │   Agent    │
   └─────────┘  └─────────┘  └────────────┘
```

The Router reads your task, decides which specialist(s) to call, gathers their outputs, and writes the final answer.

**Run it:**
```bash
python agent_multi.py --task "Analyze the project and write documentation"
```

**What's new at this level:**
- Persistent memory (session files).
- Composition of multiple agents.

---

### Level 8 — Specialized Patterns

These three agents each demonstrate one powerful, real-world technique.

#### 8a. Self-Healing Code Agent
**File:** `agent_self_healing.py`

The killer feature of LLMs is that they can read their own error messages and fix their own code. This agent:

```
1. Generate Python code from your description.
2. Run it in a sandbox subprocess.
3. If it crashes, send the error back to the LLM.
4. LLM produces fixed code.
5. Go to step 2 (up to N times).
```

This is how real code-generation tools (Cursor, GitHub Copilot CLI, Aider) actually work.

**Run it:**
```bash
python agent_self_healing.py --task "Write a function that checks if a string is a palindrome"
```

#### 8b. RAG Agent (Retrieval-Augmented Generation)
**File:** `agent_rag.py`

When your codebase is too big to fit in the LLM's context window (~128 K tokens), you can't paste everything. Instead:

```
1. INDEX:    Split every file into small chunks.
2. RETRIEVE: When asked a question, find the chunks most similar to it.
3. GENERATE: Send only those chunks to the LLM with the question.
```

This project uses **TF-IDF** (a simple keyword-similarity formula) so you don't need a fancy vector database. Real production RAG uses embeddings, but the idea is identical.

**Run it:**
```bash
python agent_rag.py --task "How does the agent loop work?"
python agent_rag.py --task "What tools are available?" --top-k 8
```

#### 8c. Generator-Critic Agent
**File:** `agent_critic.py`

Two LLM "personas" working together:

```
Generator: writes the first draft.
Critic:    grades it (Correctness / Quality / Robustness / Completeness / Performance).
Refiner:   produces v2 incorporating the critique.
```

Think of it as the LLM **doing its own code review**. The output quality is dramatically better than a single shot.

**Run it:**
```bash
python agent_critic.py --task "Write a binary search tree class" --rounds 2
python agent_critic.py --task "Write a project README" --mode text --rounds 3
```

**What's new at this level:**
- Self-correcting code (self-healing).
- Knowing how to **find** info, not just memorize it (RAG).
- Self-review (generator-critic).

---

## 5. Glossary

| Term | Beginner-friendly definition |
|------|------------------------------|
| **Agent** | An LLM in a loop with tools. |
| **API** | A doorway your code uses to talk to a service. |
| **API key** | The password that proves *you* are calling the API. Goes in `.env`. |
| **Argparse** | Python's built-in way to read `--flags` from the command line. |
| **Backoff** | "If at first you don't succeed, wait longer before trying again." |
| **Cache** | A folder where past LLM answers are saved so you don't re-pay for them. |
| **Chunk** | A small slice of a file, used in RAG. |
| **Completion** | The text the LLM gives back. Also the name of `litellm`'s main function. |
| **Context window** | How much text the LLM can "see" at once (e.g., 128 000 tokens for GPT-4). |
| **CLI** | Command-Line Interface (the terminal). |
| **Dotenv** | A file (`.env`) that stores secrets and config. Loaded by `python-dotenv`. |
| **Embedding** | A list of numbers that represents the *meaning* of a chunk of text. Not used here (we use TF-IDF instead). |
| **Function calling** | When the LLM tells you "call `read_file('foo.py')` for me." |
| **GAME** | Goal / Actions / Memory / Environment — a way to organize an agent's parts. |
| **Iteration** | One pass through the agent loop. |
| **JSON schema** | A way to describe what arguments a function takes, in JSON form. |
| **LiteLLM** | The library that hides the differences between OpenAI, Gemini, Anthropic, etc. |
| **LLM** | Large Language Model. Predicts text. |
| **Mock mode** | "Skip the real API call and pretend." Used for testing without spending money. |
| **Persona** | A "personality" you give the LLM via the system prompt. |
| **Prompt** | The text you send to the LLM. |
| **Rate limit** | "You're calling the API too fast — slow down." |
| **RAG** | Retrieval-Augmented Generation. Find relevant info → answer with that info. |
| **ReAct** | Reasoning + Acting. The LLM writes its thoughts before acting. |
| **REPL** | Read-Eval-Print Loop. A chat prompt. |
| **Sandbox** | A safe place to run untrusted code (a subprocess, a Docker container, etc.). |
| **Session** | A saved conversation. |
| **System prompt** | The "instructions" message that tells the LLM how to behave. |
| **TF-IDF** | A simple math formula for "how relevant is this chunk to this query?" |
| **Token** | A piece of a word. LLMs are billed per token. ~4 characters ≈ 1 token. |
| **Tool** | A Python function the LLM is allowed to call. |
| **Verbose** | "Show me everything" — usually a `--verbose` flag that prints raw LLM output. |

---

## 6. How to Read Any Script in This Repo

Every agent in this project follows the same skeleton. Once you can read one, you can read all of them.

```python
"""
1. MODULE DOCSTRING — what this file does, in 1-2 paragraphs.
"""

# 2. IMPORTS — load_dotenv, os, litellm, etc.
import os
from dotenv import load_dotenv
from litellm import completion
load_dotenv()

# 3. CONSTANTS — things from the .env file with sensible defaults.
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")

# 4. TOOLS — the Python functions the LLM is allowed to call.
def list_files(directory: str = ".") -> str:
    ...

# 5. TOOL SPECS — JSON schemas describing the tools to the LLM.
TOOLS = [{...}]

# 6. SYSTEM PROMPT — the persona / rules.
SYSTEM_PROMPT = "You are a helpful agent. ..."

# 7. AGENT LOOP — the main while-loop.
def run_agent(task: str) -> str:
    messages = [...]
    for step in range(max_iterations):
        response = completion(...)
        # parse, execute tool, append to messages, check done
    return final_answer

# 8. CLI — argparse for --task, --model, --verbose
def main():
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()
    run_agent(args.task)

if __name__ == "__main__":
    sys.exit(main())
```

When opening a new file:

1. Read the **module docstring** — it tells you what's special about this script.
2. Skim the **tool definitions** — that tells you what the agent can *do*.
3. Read the **system prompt** — that tells you how the agent *thinks*.
4. Read the **main loop** — that tells you how everything connects.
5. Run it with `--verbose` to see the LLM's actual responses.

That's the whole game.

---

## 7. Your First "Hello, Agent!" Exercise

Time to **do something** instead of just reading.

### Exercise 1 (5 minutes) — Run the simplest agent
```bash
python agent_loop_with_function_calling_improved.py --task "List all .md files"
```

Watch what happens. The agent:
1. Calls `list_files()`.
2. Sees the result.
3. Says "I'm done, here are the .md files."

### Exercise 2 (10 minutes) — See it think
```bash
python agent_react.py --task "Find which file has the most lines" --verbose
```

Read the `Thought:` lines. Notice how the LLM articulates a strategy.

### Exercise 3 (15 minutes) — Add your own tool
1. Open `agent_react.py`.
2. Find the `TOOL_REGISTRY` dictionary (around line 124).
3. Add a tool that returns the current date:

```python
def current_date() -> str:
    """Return today's date in YYYY-MM-DD format."""
    from datetime import date
    return date.today().isoformat()

TOOL_REGISTRY["current_date"] = current_date
```

4. Add it to the `TOOL_DESCRIPTIONS` string so the LLM knows about it.
5. Run: `python agent_react.py --task "What is today's date?"`

If the agent calls your tool and reports the right date — congratulations, you have written your first agent extension.

---

## 8. Common Mistakes Beginners Make

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Forgot to activate the venv | `ModuleNotFoundError: litellm` | Run `.venv\Scripts\activate` (or `source .venv/bin/activate`). |
| `.env` not loaded | "GEMINI_API_KEY not found" | The `.env` file must be in the same directory you run `python` from. |
| Used the wrong model name | `BadRequestError: model not found` | LiteLLM expects `gemini/gemini-1.5-flash` (note the prefix), not just `gemini-1.5-flash`. |
| Hit free tier rate limit | `RateLimitError` | Gemini free tier = 15 requests/minute. Wait a minute, or use `--mock`. |
| Infinite loop costs money | Lots of API calls | Always set `--max-iterations 5` while learning. |
| Pasted API key into code | Anyone can see it | **Never.** Always use `.env`. |
| Edited the wrong file | Changes don't show up | Make sure you're editing `*_improved.py` (the polished one), not the basic one. |

---

## 9. Where to Go Next

You've finished the guide. Here's what to do, in order of value:

1. **Build your own agent.** Read [`AGENT_BUILDING_GUIDE.md`](AGENT_BUILDING_GUIDE.md), copy `template.py`, follow the conventions in `.cursor/rules/agent-development.mdc`. Pick a problem you actually have (e.g., "an agent that summarizes my git diff").
2. **Combine patterns.** Take the ReAct prompt from `agent_react.py` and the planner from `agent_planner.py` and make a "Plan + ReAct" hybrid.
3. **Replace TF-IDF with embeddings** in `agent_rag.py`. LiteLLM supports embedding APIs. This is a huge upgrade.
4. **Add tool memory.** Right now every tool call is independent. Add a `notes.md` file the agent can write/read across iterations.
5. **Wrap an external API as a tool.** Try a weather API, a stocks API, or `requests.get(...)`. Be careful about safety.
6. **Read the readmes for each agent.** The companion `*_readme.md` files have architecture diagrams, example sessions, and pitfalls.

---

## Quick Reference Cheat Sheet

```bash
# Setup once
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
echo GEMINI_API_KEY=your-key > .env

# Test setup
python main_improved.py --mock

# Try each level
python main_improved.py
python quasi_agent_improved.py
python agent_tools_improved.py --task "List files"
python agent_loop_with_function_calling_improved.py --task "Read README"
python a_sample_agent_framework_improved.py --task "Analyze project" --verbose
python agent_react.py --task "Find functions in agent_tools.py" --verbose
python agent_planner.py --task "Document the project"
python agent_conversational.py
python agent_multi.py --task "Analyze and write docs"
python agent_self_healing.py --task "Write a prime checker"
python agent_rag.py --task "How does the loop work?"
python agent_critic.py --task "Write a stack class" --rounds 2
```

You're ready. Welcome to AI agents.
