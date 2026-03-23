# Plan-and-Execute Agent

A two-phase agent that first creates a numbered step-by-step plan, then systematically executes each step using tools. This is more structured than ReAct and works well for tasks where you can anticipate the steps ahead of time.

## Files Covered

| File | Lines | Description |
|------|-------|-------------|
| **agent_planner.py** | ~310 | Plan-and-Execute implementation with explicit planning phase (JSON plan generation), per-step execution via native function calling, step tracking, and final synthesis. |

## 🎯 What Makes Plan-and-Execute Different?

| Agent Pattern | Strategy | When to Use |
|--------------|----------|-------------|
| Basic loop | React to each step | Simple, quick tasks |
| ReAct | Reason then act per step | Complex exploration |
| **Plan-and-Execute** | **Plan all steps, then execute** | **Structured, predictable tasks** |
| GAME Framework | Goals drive action selection | Production systems |

The key insight: by committing to a plan upfront, the agent avoids aimless exploration and can track progress against milestones.

## 📊 Two-Phase Architecture

```bash
╔═══════════════════════════════════════════════════╗
║                PHASE 1: PLANNING                  ║
╠═══════════════════════════════════════════════════╣
║                                                   ║
║  User Task: "Analyze all Python files"            ║
║                                                   ║
║  LLM generates plan:                              ║
║    1. List all Python files in the directory       ║
║    2. Read main.py to understand entry point       ║
║    3. Read agent_tools.py for tool system          ║
║    4. Read quasi-agent.py for code generation      ║
║    5. Compile comprehensive project summary        ║
║                                                   ║
╠═══════════════════════════════════════════════════╣
║                PHASE 2: EXECUTION                 ║
╠═══════════════════════════════════════════════════╣
║                                                   ║
║  [>>>] Step 1: list_files() → 12 Python files     ║
║  [DONE] ✅                                        ║
║                                                   ║
║  [>>>] Step 2: read_file("main.py") → contents    ║
║  [DONE] ✅                                        ║
║                                                   ║
║  [>>>] Step 3: read_file("agent_tools.py") → ...  ║
║  [DONE] ✅                                        ║
║                                                   ║
║  ... continues for each step ...                  ║
║                                                   ║
╠═══════════════════════════════════════════════════╣
║                PHASE 3: SYNTHESIS                 ║
╠═══════════════════════════════════════════════════╣
║                                                   ║
║  All step results → LLM → Final comprehensive     ║
║  answer combining all findings                    ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
```

## 🌟 Key Features

- **Explicit Planning**: LLM generates 3-8 step plan before acting
- **Progress Tracking**: Steps marked as `[DONE]`, `[>>>]`, or `[TODO]`
- **Per-Step Execution**: Each step uses tools independently
- **Context Passing**: Earlier step results flow to later steps
- **Final Synthesis**: All results combined into a comprehensive answer
- **Native Function Calling**: Uses LLM's built-in tool selection
- **Full CLI**: `--task`, `--model`, `--verbose`

## 🛠️ Available Tools

| Tool | Description | Phase |
|------|-------------|-------|
| `list_files(directory)` | List files at a path | Execute |
| `read_file(file_name)` | Read file content | Execute |
| `write_file(file_name, content)` | Write to a file | Execute |
| `search_files(pattern, directory)` | Glob search for files | Execute |
| `mark_step_done(step_result)` | Mark current step complete | Execute |
| `finish(answer)` | Declare entire task complete | Execute |

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
python agent_planner.py

# Direct task
python agent_planner.py --task "What does each Python file in this project do?"

# Verbose (see full LLM responses and tool calls)
python agent_planner.py --task "Find all TODO comments in the codebase" --verbose

# Custom model
python agent_planner.py --model openai/gpt-4
```

## 📝 Example Session

```bash
$ python agent_planner.py --task "Analyze this project and list all function names"

  PLAN-AND-EXECUTE AGENT
======================================================================
Task : Analyze this project and list all function names
Model: gemini/gemini-1.5-flash

Phase 1: PLANNING
----------------------------------------
  1. List all Python files in the current directory
  2. Read each Python file to find function definitions
  3. Extract and organize all function names by file
  4. Compile a final summary of all functions

Phase 2: EXECUTION
----------------------------------------

>> Step 1/4: List all Python files in the current directory
    -> list_files: main.py agent_tools.py agent_react.py ...
   Result: Found 12 Python files in the directory

>> Step 2/4: Read each Python file to find function definitions
    -> read_file: (contents of main.py)
    -> read_file: (contents of agent_tools.py)
    -> read_file: (contents of agent_react.py)
   Result: Read 12 files, found function definitions in all of them

>> Step 3/4: Extract and organize all function names by file
   Result: Organized 47 functions across 12 files

>> Step 4/4: Compile a final summary of all functions
   Result: Created comprehensive function inventory

======================================================================
  TASK COMPLETE
======================================================================

main.py:
  - call_with_retries(), main()

agent_tools.py:
  - extract_markdown_block(), generate_response(), parse_action(),
    list_files(), read_file()

agent_react.py:
  - list_files(), read_file(), write_file(), search_in_file(),
    shell_command(), parse_react_response(), run_react_agent(), main()
...
```

## 🧠 How Planning Works

### Plan Generation

The planner LLM receives a system prompt that instructs it to:
1. Break the task into 3-8 concrete steps
2. Each step must be achievable with the available tools
3. The last step synthesizes results
4. Output a JSON array of step strings

```python
# Input: "Analyze this project and write a summary"
# Output:
[
    "List all Python files in the directory",
    "Read main.py to understand the entry point",
    "Read agent_tools.py to understand the tool system",
    "Read quasi-agent.py to understand code generation",
    "Write a comprehensive project summary"
]
```

### Step Execution

Each step gets its own execution context with:
- The current plan (with progress markers)
- Results from all previous steps
- The available tools
- Instructions to call `mark_step_done` when finished

### Plan Status Display

```
  [DONE] 1. List all Python files
  [DONE] 2. Read main.py
  [>>>]  3. Read agent_tools.py          ← currently executing
  [TODO] 4. Read quasi-agent.py
  [TODO] 5. Compile summary
```

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
--verbose                   # Show full LLM responses
```

## 🔍 Comparison: Plan-and-Execute vs ReAct

| Aspect | ReAct | Plan-and-Execute |
|--------|-------|-----------------|
| **Planning** | None (reason per step) | ✅ Explicit upfront plan |
| **Progress tracking** | ❌ No | ✅ Step-by-step tracking |
| **Predictability** | Low (emergent) | ✅ High (planned) |
| **Adaptability** | ✅ High (re-reasons) | Medium (follows plan) |
| **Token efficiency** | Lower (reasoning each time) | ✅ Higher (plan once) |
| **Best for** | Exploration, unknown tasks | Structured, predictable tasks |
| **Failure recovery** | Re-reasons on next step | Synthesis phase catches gaps |

### When to Use Plan-and-Execute

✅ **Use when:**
- The task has clear, predictable steps
- You want to see progress indicators
- Token efficiency matters
- The task is well-defined upfront

❌ **Use ReAct instead when:**
- The task is exploratory / open-ended
- You don't know what steps are needed
- You need to adapt heavily based on discoveries

## 💰 Cost Considerations

Plan-and-Execute typically makes:
- 1 planning call
- 2-5 tool calls per step
- 1 synthesis call

For a 5-step plan with 3 tools per step:

| Model | Planning | Execution | Synthesis | Total |
|-------|----------|-----------|-----------|-------|
| Gemini Flash | Free | Free | Free | **Free** |
| GPT-3.5-turbo | $0.002 | $0.015 | $0.002 | ~$0.02 |
| GPT-4 | $0.03 | $0.15 | $0.03 | ~$0.21 |

## 🐛 Troubleshooting

### Plan has too many / too few steps

**Solution**: The planner aims for 3-8 steps. If the task is very simple, it may generate only 2-3. For complex tasks, you might get 8. This is expected behavior.

### Step execution runs too many tool calls

**Solution**: Each step is limited to 10 tool calls. If a step is too complex, break the task into smaller pieces.

### "Step reached max tool calls without completing"

**Cause**: The step was too broad for 10 tool calls.
**Solution**: Be more specific in your task description so the planner creates more granular steps.

### Planner returns non-JSON

**Cause**: LLM didn't follow JSON format.
**Solution**: The parser has a fallback that extracts numbered lines. If that also fails, it creates a single-step plan.

## 📚 Learning Path

After mastering this agent:

1. **Add plan revision**: Let the agent modify its plan mid-execution if needed
2. **Implement parallel steps**: Execute independent steps concurrently
3. **Add dependency tracking**: Steps that depend on others run in order
4. **Combine with ReAct**: Use ReAct within each step for complex reasoning
5. **Try multi-agent**: See `agent_multi.py` for delegation patterns

## 📖 Further Reading

- [Plan-and-Solve Prompting (2023)](https://arxiv.org/abs/2305.04091) - Related research
- [LangChain Plan-and-Execute](https://python.langchain.com/docs/modules/agents/agent_types/plan_and_execute) - Framework implementation
- [BabyAGI](https://github.com/yoheinakajima/babyagi) - Task-driven autonomous agent
- [LiteLLM Documentation](https://docs.litellm.ai/)
