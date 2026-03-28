# LLMlite — Learn AI Agents from Scratch

A hands-on learning project that takes you from a single API call to full multi-agent systems, step by step. Every pattern is implemented in Python with [LiteLLM](https://docs.litellm.ai/) so you can switch between OpenAI, Gemini, and other providers with zero code changes.

---

## Why This Project?

Most agent tutorials jump straight to frameworks like LangChain or CrewAI. This project builds every concept from first principles so you actually understand what's happening under the hood.

**What you'll learn:**

- How LLM API calls work (retries, rate limits, caching)
- How to give an LLM access to tools (function calling)
- How to build an autonomous agent loop (decide → act → observe → repeat)
- Seven distinct agent architectures (ReAct, Plan-and-Execute, Conversational, Multi-Agent, Self-Healing, RAG, Generator-Critic)
- The GAME framework (Goals, Actions, Memory, Environment)
- Decorator-based tool registration for production systems
- A complete guide on how to build your own agent from scratch

---

## Quick Start

```bash
# 1. Clone and set up
git clone <repo-url> && cd LLMlite
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API key (create a .env file)
echo GEMINI_API_KEY=your-key-here > .env

# 4. Test your setup
python main_improved.py --mock

# 5. Run your first agent
python agent_react.py --task "What Python files are in this project?"
```

> **Free tier:** Google Gemini offers free API access (15 requests/minute). Get a key at [Google AI Studio](https://makersuite.google.com/app/apikey).

---

## Learning Progression

The project is organized into 8 levels. Work through them in order, or jump to any level that interests you.

```
Level 1  main.py                              Simple API call with retries
   |
Level 2  quasi-agent.py                       Multi-step workflow (generate → document → test)
   |
Level 3  llm_function_call.py                 Single-shot function calling
         agent_tools.py                       Agent loop with custom JSON parsing
   |
Level 4  agent_loop_with_function_calling.py  Native function calling in a loop
         agent_loop_with_function_calling2.py + batch file operations
   |
Level 5  a_sample_agent_framework.py          GAME architecture (Goals/Actions/Memory/Environment)
         tool_decorators.py                   @register_tool decorator pattern
   |
Level 6  agent_react.py                       ReAct: Thought → Action → Observation
         agent_planner.py                     Plan-then-Execute: Plan phase → Execute phase
   |
Level 7  agent_conversational.py              Multi-turn chat with persistent sessions
         agent_multi.py                       Router + specialist sub-agents
   |
Level 8  agent_self_healing.py                Generate code → Execute → Fix → Repeat
         agent_rag.py                         Index files → Retrieve chunks → Grounded answers
         agent_critic.py                      Generate → Critique → Refine → Repeat
```

> **New:** See [`AGENT_BUILDING_GUIDE.md`](AGENT_BUILDING_GUIDE.md) for a complete walkthrough on the process and requirements of building any new agent.

---

## All Scripts at a Glance

### Level 1: API Basics

| File | Lines | What It Teaches |
|------|-------|-----------------|
| `main.py` | 66 | Single LiteLLM call, retry with exponential backoff |
| `main_improved.py` | 219 | Structured `main()`, `--model` flag, better error messages |

```bash
python main_improved.py                    # Real API call
python main_improved.py --mock             # Test without using credits
python main_improved.py --model gpt-4      # Try different models
```

### Level 2: Multi-Step Workflow (Quasi-Agent)

| File | Lines | What It Teaches |
|------|-------|-----------------|
| `quasi-agent.py` | 247 | 3-step pipeline: generate code → add docs → add tests. Caching with SHA-256 |
| `quasi_agent_improved.py` | 579 | Dual API key support, `--no-cache`, numbered prompt requirements |

```bash
python quasi_agent_improved.py             # Interactive: describe a function
python quasi_agent_improved.py --no-cache  # Force fresh API calls
```

### Level 3: Function Calling

| File | Lines | What It Teaches |
|------|-------|-----------------|
| `llm_function_call.py` | 99 | Single-shot native function call (no loop) |
| `llm_function_improved.py` | 204 | Better structure, `pathlib`, file size limits |
| `agent_tools.py` | 171 | Agent loop with custom ` ```action` JSON block parsing |
| `agent_tools_improved.py` | 677 | Adds `write_file`, `search_files`, dynamic schema injection, verbose mode |

```bash
python agent_tools_improved.py --task "Find all Python files"
python agent_tools_improved.py --task "Read README and summarize it" --verbose
```

### Level 4: Native Function Calling Agents

| File | Lines | What It Teaches |
|------|-------|-----------------|
| `agent_loop_with_function_calling.py` | 148 | Clean loop using LLM's built-in `tool_calls` — no custom parsing |
| `agent_loop_with_function_calling_improved.py` | 521 | Adds `search_files`, structured code, full CLI |
| `agent_loop_with_function_calling2.py` | 251 | Batch ops: `read_all_files()` reads entire directory at once |
| `agent_loop_with_function_calling2_improved.py` | 633 | Per-file error isolation, 10 MB limit, result summaries |

```bash
python agent_loop_with_function_calling_improved.py --task "Read all .md files"
python agent_loop_with_function_calling2_improved.py --task "Summarize the project"
```

### Level 5: GAME Framework

| File | Lines | What It Teaches |
|------|-------|-----------------|
| `a_sample_agent_framework.py` | 415 | Full GAME architecture: Goal, Action, Memory, Environment classes |
| `a_sample_agent_framework_improved.py` | 906 | Factory function, `requires_confirmation`, CLI, memory management |
| `tool_decorators.py` | 593 | `@register_tool` decorator, auto-generated JSON schemas, tag-based filtering |

```bash
python a_sample_agent_framework_improved.py --task "Analyze Python files" --verbose
python tool_decorators.py                  # Runs built-in demo
```

### Level 6: Advanced Agent Patterns

| File | Lines | Pattern | Key Idea |
|------|-------|---------|----------|
| `agent_react.py` | 389 | **ReAct** | LLM must produce `Thought → Action → Observation` every turn. Explicit reasoning improves decisions. |
| `agent_planner.py` | 457 | **Plan-and-Execute** | Phase 1: LLM generates a numbered plan. Phase 2: execute each step with tools. Tracks `[DONE]/[TODO]` progress. |

```bash
# ReAct — great for exploratory tasks
python agent_react.py --task "Find all functions in agent_tools.py"
python agent_react.py --task "Search for TODO comments across the project" --verbose

# Plan-and-Execute — great for structured, predictable tasks
python agent_planner.py --task "Analyze each Python file and summarize the project"
python agent_planner.py --task "Find all imports used across the codebase" --verbose
```

### Level 7: Production Patterns

| File | Lines | Pattern | Key Idea |
|------|-------|---------|----------|
| `agent_conversational.py` | 397 | **Conversational** | Multi-turn REPL chat. Sessions saved to disk as JSON. Resume with `--resume latest`. |
| `agent_multi.py` | 456 | **Multi-Agent** | Router delegates to 3 specialists (Code Analyst, Writer, Researcher). Context flows between agents. |

```bash
# Conversational — persistent multi-turn chat
python agent_conversational.py                     # Start new session
python agent_conversational.py --resume latest     # Resume last conversation
python agent_conversational.py --list-sessions     # See all saved sessions

# Multi-Agent — divide and conquer
python agent_multi.py --task "Analyze this project and write documentation"
python agent_multi.py --task "Find all agent patterns and compare them" --verbose
```

### Level 8: Specialized Agents

| File | Lines | Pattern | Key Idea |
|------|-------|---------|----------|
| `agent_self_healing.py` | ~250 | **Self-Healing** | Generates code, executes in sandbox, feeds errors back to LLM for automatic fixes. |
| `agent_rag.py` | ~290 | **RAG** | Indexes files into chunks, retrieves relevant pieces via TF-IDF, generates grounded answers with citations. |
| `agent_critic.py` | ~260 | **Generator-Critic** | Two-persona loop: Generator creates output, Critic reviews it, Refiner improves it. Supports code/text/plan modes. |

```bash
# Self-Healing — code that fixes itself
python agent_self_healing.py --task "Write a function to check if a number is prime"
python agent_self_healing.py --task "Implement merge sort" --max-retries 5 --save sort.py

# RAG — Q&A grounded in your actual codebase
python agent_rag.py --task "How does the agent loop work?"
python agent_rag.py --task "What tools are available?" --top-k 8

# Generator-Critic — higher quality through self-review
python agent_critic.py --task "Write a binary search tree class"
python agent_critic.py --task "Write a project README" --mode text --rounds 3
python agent_critic.py --task "Plan a REST API migration" --mode plan
```

---

## Agent Pattern Comparison

| Pattern | File | Reasoning | Planning | Memory | Multi-Turn | Best For |
|---------|------|-----------|----------|--------|------------|----------|
| Basic loop | `agent_tools.py` | Hidden | None | In-memory | No | Simple tasks |
| Function calling | `agent_loop_*.py` | Hidden | None | In-memory | No | Reliable tool use |
| GAME framework | `a_sample_agent_framework.py` | Hidden | Goal-driven | Typed Memory class | No | Production systems |
| **ReAct** | `agent_react.py` | **Explicit** | None | In-memory | No | Exploration, debugging |
| **Plan-and-Execute** | `agent_planner.py` | Per-step | **Explicit plan** | In-memory | No | Structured tasks |
| **Conversational** | `agent_conversational.py` | Hidden | None | **Persistent (disk)** | **Yes** | Assistant / chat |
| **Multi-Agent** | `agent_multi.py` | Per-agent | **Router decides** | Per-agent | No | Complex, multi-skill tasks |
| **Self-Healing** | `agent_self_healing.py` | Fix-focused | None | Error history | No | Code that must execute |
| **RAG** | `agent_rag.py` | Grounded | None | TF-IDF index | No | Q&A over documents |
| **Generator-Critic** | `agent_critic.py` | Two-persona | None | Critique history | No | High-quality output |

### When to Use What

- **"I just want it to work"** → `agent_loop_with_function_calling_improved.py`
- **"I need to see its reasoning"** → `agent_react.py`
- **"The task has clear steps"** → `agent_planner.py`
- **"I want to have a conversation"** → `agent_conversational.py`
- **"The task needs multiple skills"** → `agent_multi.py`
- **"I need code that actually runs"** → `agent_self_healing.py`
- **"I need answers grounded in my files"** → `agent_rag.py`
- **"Quality matters more than speed"** → `agent_critic.py`
- **"I'm building a production system"** → `a_sample_agent_framework_improved.py` + `tool_decorators.py`
- **"I want to build my own agent"** → Start with [`AGENT_BUILDING_GUIDE.md`](AGENT_BUILDING_GUIDE.md)

---

## Documentation Index

Every agent has a dedicated readme with architecture diagrams, example sessions, troubleshooting, and cost estimates.

### Per-Script Guides

| Guide | Covers |
|-------|--------|
| [`main_readme.md`](main_readme.md) | API basics, retry logic, mock mode |
| [`quasi_agent_readme.md`](quasi_agent_readme.md) | Multi-step workflows, caching strategy |
| [`llm_function_call_guide.md`](llm_function_call_guide.md) | Function calling fundamentals |
| [`agent_tools_readme.md`](agent_tools_readme.md) | Custom JSON parsing, tool schemas |
| [`agent_loop_with_function_calling_readme.md`](agent_loop_with_function_calling_readme.md) | Native function calling, tool registry |
| [`agent_loop_with_function_calling2_readme.md`](agent_loop_with_function_calling2_readme.md) | Batch operations, efficiency |
| [`a_sample_agent_framework_readme.md`](a_sample_agent_framework_readme.md) | GAME architecture, `@register_tool`, `PythonActionRegistry` |
| [`agent_react_readme.md`](agent_react_readme.md) | ReAct pattern, Thought/Action parsing, shell commands |
| [`agent_planner_readme.md`](agent_planner_readme.md) | Plan-and-Execute, step tracking, synthesis |
| [`agent_conversational_readme.md`](agent_conversational_readme.md) | Persistent sessions, resume, in-chat commands |
| [`agent_multi_readme.md`](agent_multi_readme.md) | Router + specialists, context flow, adding agents |
| [`agent_self_healing_readme.md`](agent_self_healing_readme.md) | Self-healing code generation, sandbox execution |
| [`agent_rag_readme.md`](agent_rag_readme.md) | RAG pattern, TF-IDF retrieval, grounded answers |
| [`agent_critic_readme.md`](agent_critic_readme.md) | Generator-Critic pattern, multi-mode refinement |

### Guides

| Guide | Covers |
|-------|--------|
| [`AGENT_BUILDING_GUIDE.md`](AGENT_BUILDING_GUIDE.md) | **Complete walkthrough for building a new agent** — requirements, pattern selection, tool design, loop structure, memory, safety, testing, and common pitfalls |

### Cross-Cutting Comparisons

| Guide | Covers |
|-------|--------|
| [`1_complete_comparison.md`](1_complete_comparison.md) | Progression from API calls → quasi-agent → tool agent |
| [`2_agents_framework_comparison.md`](2_agents_framework_comparison.md) | Loop agents vs GAME architecture |
| [`2_readme.md`](2_readme.md) | Project-wide script inventory (Levels 1–5) |

### PDF Versions

PDF versions of the new agent readmes are available for offline reading:
`agent_react_readme.pdf`, `agent_planner_readme.pdf`, `agent_conversational_readme.pdf`, `agent_multi_readme.pdf`

Generate more with: `python md_to_pdf.py --all`

---

## Project Structure

```
LLMlite/
│
├── .env                                         # API keys (DO NOT commit)
├── .gitignore                                   # Ignores .env, caches, sessions
├── requirements.txt                             # python-dotenv, litellm, PyPDF2
│
│  ── Level 1: API Basics ──
├── main.py                                      # Simple API test
├── main_improved.py                             # Structured version
│
│  ── Level 2: Multi-Step Workflow ──
├── quasi-agent.py                               # Fixed 3-step pipeline
├── quasi_agent_improved.py                      # Enhanced with --no-cache
│
│  ── Level 3: Function Calling ──
├── llm_function_call.py                         # Single-shot function call
├── llm_function_improved.py                     # Improved version
├── agent_tools.py                               # Custom JSON parsing agent
├── agent_tools_improved.py                      # + write_file, search_files
│
│  ── Level 4: Native Function Calling ──
├── agent_loop_with_function_calling.py          # Simple native loop
├── agent_loop_with_function_calling_improved.py # + search_files, CLI
├── agent_loop_with_function_calling2.py         # + batch read_all_files
├── agent_loop_with_function_calling2_improved.py# + size limits, summaries
│
│  ── Level 5: GAME Framework ──
├── a_sample_agent_framework.py                  # Full GAME architecture
├── a_sample_agent_framework_improved.py         # Factory, CLI, verbose
├── tool_decorators.py                           # @register_tool + tag filtering
│
│  ── Level 6: Advanced Patterns ──
├── agent_react.py                               # ReAct (Thought→Action→Observation)
├── agent_planner.py                             # Plan-and-Execute (plan→steps→synthesize)
│
│  ── Level 7: Production Patterns ──
├── agent_conversational.py                      # Multi-turn chat + persistent sessions
├── agent_multi.py                               # Router + specialist sub-agents
│
│  ── Level 8: Specialized Agents ──
├── agent_self_healing.py                        # Generate → Execute → Fix loop
├── agent_rag.py                                 # Index → Retrieve → Generate (RAG)
├── agent_critic.py                              # Generate → Critique → Refine loop
│
│  ── Utilities ──
├── template.py                                  # Boilerplate for new scripts
├── md_to_pdf.py                                 # Markdown → PDF converter
│
│  ── Documentation ──
├── README.md                                    # This file
├── 1_complete_comparison.md                     # Levels 1-3 comparison
├── 2_agents_framework_comparison.md             # Levels 4-5 comparison
├── 2_readme.md                                  # Script inventory (Levels 1-5)
├── main_readme.md                               # Guide: API basics
├── quasi_agent_readme.md                        # Guide: multi-step workflows
├── llm_function_call_guide.md                   # Guide: function calling
├── agent_tools_readme.md                        # Guide: custom JSON agents
├── agent_loop_with_function_calling_readme.md   # Guide: native function calling
├── agent_loop_with_function_calling2_readme.md  # Guide: batch operations
├── a_sample_agent_framework_readme.md           # Guide: GAME framework
├── agent_react_readme.md                        # Guide: ReAct pattern
├── agent_planner_readme.md                      # Guide: Plan-and-Execute
├── agent_conversational_readme.md               # Guide: conversational agent
├── agent_multi_readme.md                        # Guide: multi-agent orchestrator
├── agent_self_healing_readme.md                 # Guide: self-healing code agent
├── agent_rag_readme.md                          # Guide: RAG agent
├── agent_critic_readme.md                       # Guide: generator-critic agent
├── AGENT_BUILDING_GUIDE.md                      # How to build your own agent
│
│  ── Generated Output (from quasi-agent) ──
├── factorial.py                                 # Example generated code
├── calculate_fibonacci_sequence_u.py
├── given_a_set_of_nonoverlapping_.py
├── maximum_running_time_of_n_comp.py
├── median_of_the_2_sorted_arrays.py
├── regular_expression_matching.py
│
│  ── Cursor IDE Rules ──
└── .cursor/rules/
    ├── project-conventions.mdc                  # Project-wide coding standards
    ├── agent-development.mdc                    # Rules for creating new agents
    └── code-quality.mdc                         # Security, style, LLM call safety
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required: at least one API key
GEMINI_API_KEY=your-gemini-key-here
OPENAI_API_KEY=your-openai-key-here

# Optional: customize defaults
DEFAULT_MODEL=gemini/gemini-1.5-flash
DEFAULT_MAX_ITERATIONS=10
DEFAULT_MAX_TOKENS=1024

# Optional: caching (used by quasi-agent)
LLM_CACHE_DIR=.llm_cache

# Optional: conversational agent session storage
SESSION_DIR=.agent_sessions
```

### Common CLI Flags

Every improved script supports these flags:

| Flag | Description | Example |
|------|-------------|---------|
| `--task "..."` | Run with a specific task (skip interactive prompt) | `--task "List Python files"` |
| `--model NAME` | Override the LLM model | `--model openai/gpt-4` |
| `--verbose` | Show full LLM responses and tool details | `--verbose` |
| `--max-iterations N` | Cap the agent loop | `--max-iterations 5` |
| `--mock` | Skip real API calls (main.py, quasi-agent) | `--mock` |

---

## Cost Estimates

| Model | Cost per Call | 5-Step Task | Free Tier? |
|-------|-------------|-------------|------------|
| `gemini/gemini-1.5-flash` | Free | Free | Yes (15 RPM) |
| `gpt-3.5-turbo` | ~$0.002 | ~$0.01 | No |
| `gpt-4` | ~$0.03 | ~$0.15 | No |
| `gpt-4o` | ~$0.01 | ~$0.05 | No |

**Tips to save money:**
1. Start with `gemini/gemini-1.5-flash` (free)
2. Use `--mock` mode when testing code changes
3. Set `--max-iterations 5` to cap runaway loops
4. Use batch operations (`agent_loop_with_function_calling2`) for multi-file tasks
5. Enable caching (`quasi-agent.py`) to avoid duplicate calls

---

## Suggested Learning Path

### Week 1: Foundations

```bash
python main_improved.py --mock                  # Understand API call structure
python main_improved.py                         # Make a real call
python quasi_agent_improved.py                  # See multi-step orchestration
```

Read: `main_readme.md` → `quasi_agent_readme.md`

### Week 2: Tool-Using Agents

```bash
python llm_function_call.py                     # One-shot function call
python agent_tools_improved.py --task "List files" --verbose   # Custom parsing
python agent_loop_with_function_calling_improved.py --task "Read README" # Native
```

Read: `llm_function_call_guide.md` → `agent_tools_readme.md` → `agent_loop_with_function_calling_readme.md`

### Week 3: Agent Architecture

```bash
python agent_loop_with_function_calling2_improved.py --task "Read all files"
python a_sample_agent_framework_improved.py --verbose
python tool_decorators.py
```

Read: `agent_loop_with_function_calling2_readme.md` → `a_sample_agent_framework_readme.md`

### Week 4: Advanced Patterns

```bash
python agent_react.py --task "Summarize all Python files" --verbose
python agent_planner.py --task "Analyze the project structure"
python agent_conversational.py
python agent_multi.py --task "Document this project"
```

Read: `agent_react_readme.md` → `agent_planner_readme.md` → `agent_conversational_readme.md` → `agent_multi_readme.md`

### Week 5: Specialized Patterns

```bash
python agent_self_healing.py --task "Write a palindrome checker"
python agent_rag.py --task "What patterns are used in this project?"
python agent_critic.py --task "Write a stack data structure" --rounds 2
```

Read: `agent_self_healing_readme.md` → `agent_rag_readme.md` → `agent_critic_readme.md`

### Week 6: Build Your Own

Read [`AGENT_BUILDING_GUIDE.md`](AGENT_BUILDING_GUIDE.md) first, then:
1. Add a new tool to an existing agent
2. Create a new specialist in `agent_multi.py`
3. Combine ReAct reasoning with Plan-and-Execute structure
4. Build a domain-specific agent for your own use case

---

## Key Concepts Reference

| Concept | Where It's Used | Description |
|---------|----------------|-------------|
| **Retry + backoff** | `main.py` | Handles rate limits by waiting exponentially longer |
| **Caching** | `quasi-agent.py` | SHA-256 keyed file cache avoids duplicate API calls |
| **Conversation memory** | All agents | Chat history passed to LLM so it remembers context |
| **Custom parsing** | `agent_tools.py` | LLM outputs ` ```action {...}` ``` blocks parsed with regex |
| **Native function calling** | `agent_loop_*.py` | LLM returns structured `tool_calls` — no parsing needed |
| **GAME architecture** | `a_sample_agent_framework.py` | Goals + Actions + Memory + Environment as classes |
| **@register_tool** | `tool_decorators.py` | Decorator auto-generates JSON schemas from type hints |
| **ReAct** | `agent_react.py` | Forced Thought → Action → Observation loop |
| **Plan-and-Execute** | `agent_planner.py` | LLM creates plan upfront, then executes step by step |
| **Session persistence** | `agent_conversational.py` | Conversations saved to `.agent_sessions/` as JSON |
| **Multi-agent delegation** | `agent_multi.py` | Router assigns work to Code Analyst / Writer / Researcher |
| **Self-healing loop** | `agent_self_healing.py` | Generate → execute → catch error → fix → retry |
| **TF-IDF retrieval** | `agent_rag.py` | Keyword-based search over file chunks, no vector DB needed |
| **Generator-Critic** | `agent_critic.py` | Two-persona refinement: generate, critique (5 categories), refine |

---

## Contributing

To add a new agent:

1. Read [`AGENT_BUILDING_GUIDE.md`](AGENT_BUILDING_GUIDE.md) for the full process
2. Copy `template.py` as a starting point
3. Follow the conventions in `.cursor/rules/agent-development.mdc`
4. Include: module docstring, `argparse` CLI, `--task`/`--model`/`--verbose` flags
5. Create a companion `_readme.md`
6. Generate PDF with `python md_to_pdf.py your_agent_readme.md`
7. Update this README with the new entry

---

## Requirements

- **Python 3.8+**
- **Dependencies:** `pip install -r requirements.txt`
  - `python-dotenv` — loads `.env` files
  - `litellm` — unified LLM API (OpenAI, Gemini, Anthropic, etc.)
  - `PyPDF2` — PDF reading (used by some tools)

---

## License

This project is for educational purposes. Use it to learn, experiment, and build your own agents.
