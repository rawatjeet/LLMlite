# Multi-Agent Orchestrator

A delegation-pattern agent system where a **Router Agent** analyzes the user's task and delegates work to specialized **sub-agents** (Code Analyst, Writer, Researcher). Each specialist has its own system prompt and tool access. Results flow between agents and are synthesized into a final answer.

## Files Covered

| File | Lines | Description |
|------|-------|-------------|
| **agent_multi.py** | ~340 | Multi-agent orchestrator with Router (LLM-based delegation planning), 3 specialist sub-agents, context passing between agents, and final synthesis phase. Uses native function calling. |

## 🎯 What Makes Multi-Agent Different?

| Pattern | Agents | Decision Making |
|---------|--------|----------------|
| Single agent | 1 agent, all tools | One LLM does everything |
| **Multi-agent** | **1 router + N specialists** | **Router delegates, specialists execute** |

The advantage: each specialist has a focused system prompt and limited tools, making it better at its specific job. The router handles high-level task decomposition.

## 📊 Architecture

```bash
╔═══════════════════════════════════════════════════════════╗
║                    ROUTER AGENT                          ║
║                                                          ║
║  Input: "Analyze the project and write documentation"    ║
║                                                          ║
║  Delegation Plan:                                        ║
║    1. [Researcher]    → Find all Python files             ║
║    2. [Code Analyst]  → Analyze code architecture         ║
║    3. [Writer]        → Write comprehensive docs          ║
║                                                          ║
╠═════════════╦═══════════════╦════════════════════════════╣
║             ║               ║                            ║
║  ┌──────────▼──┐  ┌────────▼────────┐  ┌───────────────▼┐
║  │ RESEARCHER  │  │  CODE ANALYST   │  │    WRITER      │
║  │             │  │                 │  │                │
║  │ Tools:      │  │ Tools:          │  │ Tools:         │
║  │ • list_files│  │ • list_files    │  │ • list_files   │
║  │ • read_file │  │ • read_file     │  │ • read_file    │
║  │ • search    │  │ • search_files  │  │ • write_file   │
║  │ • done      │  │ • done          │  │ • done         │
║  │             │  │                 │  │                │
║  │ Focus:      │  │ Focus:          │  │ Focus:         │
║  │ Finding &   │  │ Understanding   │  │ Creating       │
║  │ gathering   │  │ code structure  │  │ documentation  │
║  └──────┬──────┘  └────────┬────────┘  └───────┬────────┘
║         │                  │                    │         ║
║         └──────────────────┼────────────────────┘         ║
║                            │                              ║
║                   ┌────────▼────────┐                     ║
║                   │   SYNTHESIS     │                     ║
║                   │                 │                     ║
║                   │ Combine results │                     ║
║                   │ from all agents │                     ║
║                   │ into final      │                     ║
║                   │ answer          │                     ║
║                   └─────────────────┘                     ║
╚═══════════════════════════════════════════════════════════╝
```

## 🌟 Key Features

- **Intelligent Routing**: LLM-based router creates optimal delegation plan
- **3 Specialist Agents**: Code Analyst, Writer, Researcher
- **Context Passing**: Results from earlier agents flow to later ones
- **Final Synthesis**: All results combined into comprehensive answer
- **Per-Agent Tools**: Each specialist gets only the tools it needs
- **Native Function Calling**: Reliable tool selection within each agent
- **Full CLI**: `--task`, `--model`, `--verbose`

## 🤖 Specialist Agents

### Code Analyst

| Attribute | Value |
|-----------|-------|
| **Focus** | Reading and analyzing source code |
| **Tools** | `list_files`, `read_file`, `search_files`, `done` |
| **Best for** | Understanding code structure, finding patterns, analyzing architecture |

### Writer

| Attribute | Value |
|-----------|-------|
| **Focus** | Creating documentation, summaries, and text content |
| **Tools** | `list_files`, `read_file`, `write_file`, `done` |
| **Best for** | README files, documentation, summaries, reports |

### Researcher

| Attribute | Value |
|-----------|-------|
| **Focus** | Searching files and gathering specific information |
| **Tools** | `list_files`, `read_file`, `search_files`, `done` |
| **Best for** | Finding specific files, patterns, data, or information |

## 📋 Prerequisites

- **Python 3.8+**
- **API Key**: Gemini (recommended) or OpenAI
- Install dependencies: `pip install -r requirements.txt`

## 🚀 Quick Start

### Installation

```bash
pip install litellm python-dotenv
echo "GEMINI_API_KEY=your-key-here" > .env
```

### Basic Usage

```bash
# Interactive mode
python agent_multi.py

# Direct task
python agent_multi.py --task "Analyze this project and write documentation"

# Verbose (see all sub-agent tool calls)
python agent_multi.py --task "Find all functions in the codebase" --verbose

# Custom model
python agent_multi.py --model openai/gpt-4
```

## 📝 Example Session

```bash
$ python agent_multi.py --task "Analyze this project and create a summary"

======================================================================
  MULTI-AGENT ORCHESTRATOR
======================================================================
Task : Analyze this project and create a summary
Model: gemini/gemini-1.5-flash

Phase 1: ROUTING
----------------------------------------
  1. [Researcher] Find all Python files and categorize them
  2. [Code Analyst] Analyze the main agent patterns used
  3. [Writer] Create a comprehensive project summary

Phase 2: DELEGATION
----------------------------------------

  [Researcher] Starting: Find all Python files and categorize them
  [Researcher] Done (450 chars)

  [Code Analyst] Starting: Analyze the main agent patterns used
  [Code Analyst] Done (1200 chars)

  [Writer] Starting: Create a comprehensive project summary
  [Writer] Done (2100 chars)

Phase 3: SYNTHESIS
----------------------------------------

======================================================================
  TASK COMPLETE
======================================================================

# LLMlite Project Summary

This project is a learning-oriented collection of AI agent implementations
using Python and LiteLLM. It demonstrates a progression of agent patterns:

1. **Simple API calls** (main.py) - Basic LLM interaction
2. **Quasi-agents** (quasi-agent.py) - Multi-step code generation
3. **Function calling** (agent_loop_*.py) - Native tool invocation
4. **Custom parsing** (agent_tools.py) - Manual JSON action blocks
5. **GAME framework** (a_sample_agent_framework.py) - Full architecture
6. **ReAct** (agent_react.py) - Reasoning + Acting pattern
7. **Plan-and-Execute** (agent_planner.py) - Two-phase planning
8. **Conversational** (agent_conversational.py) - Persistent chat
9. **Multi-agent** (agent_multi.py) - Delegation orchestration
...
```

## 🧠 How Routing Works

### Router Decision Process

The Router receives the user task and decides which specialists to use:

```python
# Router's input
"Analyze this project and create a summary"

# Router's output (JSON array)
[
    {"agent": "researcher", "task": "Find all Python files and list them"},
    {"agent": "code_analyst", "task": "Read key files and analyze patterns"},
    {"agent": "writer", "task": "Write a comprehensive project summary"}
]
```

### Context Flow Between Agents

Each agent receives results from all previous agents as context:

```
Agent 1 (Researcher):
  Input: "Find all Python files"
  Output: "Found 12 files: main.py, agent_tools.py, ..."

Agent 2 (Code Analyst):
  Input: "Analyze code patterns"
  Context: "Previous: Found 12 files: main.py, ..."    ← from Agent 1
  Output: "The project uses 5 agent patterns: ..."

Agent 3 (Writer):
  Input: "Write project summary"
  Context: "Found 12 files...\nUses 5 patterns..."      ← from Agents 1+2
  Output: "# LLMlite Project Summary\n..."
```

### Sub-Agent Execution

Each sub-agent runs its own tool-calling loop (up to 15 tool calls):

```
[Code Analyst] Tool: list_files() → 12 files
[Code Analyst] Tool: read_file("main.py") → contents
[Code Analyst] Tool: read_file("agent_react.py") → contents
[Code Analyst] Tool: done("Analysis: The project uses...")
```

The sub-agent calls `done` when it's finished, returning its findings.

## ⚙️ Configuration

### Environment Variables

```env
GEMINI_API_KEY=your-key
OPENAI_API_KEY=your-key
DEFAULT_MODEL=gemini/gemini-1.5-flash
DEFAULT_MAX_TOKENS=2048
```

### CLI Options

```bash
--task "Your task"          # Task description
--model MODEL_NAME          # LLM model to use
--verbose                   # Show all sub-agent tool calls
```

## 🔍 Comparison with Other Agents

| Feature | Single Agent | **Multi-Agent** |
|---------|-------------|-----------------|
| **Agents** | 1 | 1 router + 3 specialists |
| **System prompts** | 1 generic | 4 specialized |
| **Tool access** | All tools | Per-agent filtered tools |
| **Focus** | General purpose | ✅ Specialist focus |
| **Complex tasks** | May struggle | ✅ Divide and conquer |
| **API calls** | 5-15 | 10-30 (more but better) |
| **Result quality** | Good | ✅ Higher (specialized) |

## 💰 Cost Considerations

Multi-agent uses more API calls but produces better results:

| Phase | Calls | Cost (GPT-4) |
|-------|-------|-------------|
| Routing | 1 | ~$0.03 |
| Sub-agent 1 | 3-5 | ~$0.10 |
| Sub-agent 2 | 3-5 | ~$0.10 |
| Sub-agent 3 | 3-5 | ~$0.10 |
| Synthesis | 1 | ~$0.03 |
| **Total** | **11-17** | **~$0.36** |

**Tip**: Use Gemini Flash for free-tier usage, or use GPT-4 for higher quality on complex tasks.

## 🐛 Troubleshooting

### Router delegates to unknown agent

**Cause**: LLM generated an agent name not in `AGENTS`.
**Solution**: Falls back to `code_analyst`. Add more specialists by extending the `AGENTS` dictionary.

### Sub-agent doesn't call "done"

**Cause**: Agent reached max tool calls (15) without finishing.
**Solution**: Increase `max_tool_calls` in `run_sub_agent()`, or make the task more specific.

### Results don't flow between agents

**Cause**: Context from previous agents is truncated (2000 chars per result).
**Solution**: Increase the truncation limit in the context-passing logic, or use the `--verbose` flag to diagnose.

### Synthesis is too generic

**Cause**: Too much information or too little from sub-agents.
**Solution**: Make the routing tasks more specific. The synthesis quality depends on the sub-agent results.

## 🔧 Adding a New Specialist

### Step 1: Define the Agent

```python
AGENTS["database_admin"] = {
    "name": "Database Admin",
    "system_prompt": (
        "You are a database administration agent. Your job is to "
        "analyze SQL files, database schemas, and data models..."
    ),
    "tools": ["list_files", "read_file", "search_files", "done"],
}
```

### Step 2: Update Router Prompt

Add the new specialist to `ROUTER_SYSTEM_PROMPT`:

```python
ROUTER_SYSTEM_PROMPT = """...
Available specialists:
- code_analyst: Reads and analyzes source code
- writer: Creates documentation
- researcher: Searches and gathers information
- database_admin: Analyzes database schemas and SQL   ← NEW
..."""
```

That's it! The router will automatically learn to delegate database tasks to the new specialist.

## 📊 When to Use Multi-Agent

### Best For

✅ **Complex tasks** requiring multiple skills (analysis + writing)
✅ **Large codebases** where focused reading is better
✅ **Documentation generation** (research → analyze → write)
✅ **Code reviews** (find files → analyze patterns → write report)

### Not Ideal For

❌ **Simple tasks** (single agent is faster and cheaper)
❌ **Very quick lookups** (just use `agent_tools.py`)
❌ **Token-sensitive environments** (multi-agent uses more tokens)

## 📚 Learning Path

After mastering this agent:

1. **Add more specialists**: Database admin, test writer, security auditor
2. **Parallel execution**: Run independent sub-agents concurrently
3. **Agent communication**: Let sub-agents talk to each other
4. **Hierarchical agents**: Sub-agents that delegate to their own sub-agents
5. **Voting/consensus**: Multiple agents solve the same problem, pick the best answer

## 📖 Further Reading

- [AutoGen (Microsoft)](https://microsoft.github.io/autogen/) - Multi-agent conversation framework
- [CrewAI](https://www.crewai.com/) - Framework for multi-agent orchestration
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Stateful multi-agent graphs
- [Mixture of Agents (2024)](https://arxiv.org/abs/2406.04692) - Research on agent collaboration
- [LiteLLM Documentation](https://docs.litellm.ai/)
