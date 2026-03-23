# ReAct Agent (Reasoning + Acting)

An agent that implements the ReAct pattern from the landmark paper [*ReAct: Synergizing Reasoning and Acting in Language Models*](https://arxiv.org/abs/2210.03629). The LLM is forced to produce explicit **Thought → Action → Observation** triples on every turn, leading to more reliable multi-step problem solving.

## Files Covered

| File | Lines | Description |
|------|-------|-------------|
| **agent_react.py** | ~290 | ReAct implementation with text-based Thought/Action parsing, 6 tools (list_files, read_file, write_file, search_in_file, shell_command, finish), regex-based response parser, and full CLI. |

## 🎯 What Makes ReAct Different?

Unlike other agents in this project that use native function calling or custom JSON blocks, ReAct forces the LLM to **think out loud** before every action:

| Approach | Format | Reasoning Visible? |
|----------|--------|-------------------|
| Basic agent loop | `tool_calls[0]` | ❌ No |
| Custom JSON parsing | ` ```action { ... } ``` ` | ⚠️ Optional |
| **ReAct (this)** | `Thought: ... Action: ...` | ✅ Always |

This explicit reasoning step significantly improves decision quality because the model must articulate *why* it's choosing an action before choosing it.

## 📊 The ReAct Loop

```bash
┌─────────────────────────────────────────┐
│  User provides task                     │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  Thought: "I need to first list the     │
│  files to see what's available..."      │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  Action: list_files(directory=".")      │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  Observation: "main.py\nagent.py\n..."  │
│  (fed back to the LLM as context)      │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  Thought: "Now I should read agent.py   │
│  to understand the agent code..."       │
└──────────────┬──────────────────────────┘
               ↓
       ... continues until ...
               ↓
┌─────────────────────────────────────────┐
│  Action: finish("Here is the summary") │
│  ✅ TASK COMPLETE                       │
└─────────────────────────────────────────┘
```

## 🌟 Key Features

- **Explicit Reasoning**: Every step begins with a Thought explaining the logic
- **6 Built-in Tools**: File ops, regex search, safe shell commands, and finish
- **Regex Response Parser**: Robust parsing of Thought/Action format
- **Safe Shell Commands**: Allowlist of read-only commands (ls, grep, head, etc.)
- **Full CLI**: `--task`, `--model`, `--max-iterations`, `--verbose`
- **Configurable**: Environment variables for model, tokens, iterations

## 🛠️ Available Tools

| Tool | Description | Example |
|------|-------------|---------|
| `list_files(directory)` | List files and directories | `list_files(".")` |
| `read_file(file_name)` | Read file content (max 50 KB) | `read_file("main.py")` |
| `write_file(file_name, content)` | Write text to a file | `write_file("out.txt", "hello")` |
| `search_in_file(file_name, pattern)` | Regex search inside a file | `search_in_file("main.py", "def .*")` |
| `shell_command(command)` | Run safe read-only shell command | `shell_command("wc -l *.py")` |
| `finish(answer)` | End the loop with final answer | `finish("Found 5 files")` |

### Shell Command Safety

Only these read-only command prefixes are allowed:
`ls`, `dir`, `cat`, `head`, `tail`, `wc`, `find`, `grep`, `type`, `echo`

Commands have a 10-second timeout to prevent hangs.

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
python agent_react.py

# Direct task
python agent_react.py --task "Find all Python files and summarize what each does"

# Verbose (shows full LLM output)
python agent_react.py --task "What functions are in agent_tools.py?" --verbose

# Custom model and iterations
python agent_react.py --model openai/gpt-4 --max-iterations 20
```

## 📝 Example Sessions

### Example 1: File Analysis

```bash
$ python agent_react.py --task "What Python files are in this project?"

--- Step 1 ---
Thought: I need to list the files in the current directory to find Python files.
Action : list_files({'directory': '.'})
Observation: main.py agent_tools.py agent_react.py quasi-agent.py ...

--- Step 2 ---
Thought: I can see multiple .py files. Let me compile the list and provide the answer.
Action : finish({'answer': 'Found 12 Python files: main.py, agent_tools.py, ...'})

  TASK COMPLETE
Answer:
Found 12 Python files: main.py, agent_tools.py, agent_react.py, ...
```

### Example 2: Code Search

```bash
$ python agent_react.py --task "Find all functions that use litellm.completion"

--- Step 1 ---
Thought: I should list Python files first, then search each for litellm.completion calls.
Action : list_files({'directory': '.'})
Observation: main.py agent_tools.py quasi-agent.py ...

--- Step 2 ---
Thought: Let me search main.py for completion calls.
Action : search_in_file({'file_name': 'main.py', 'pattern': 'completion'})
Observation: 2 match(es) in main.py:
  L29: return completion(model=model, api_key=api_key, messages=messages)
  ...

--- Step 3 ---
Thought: Found matches. Let me check agent_tools.py next.
Action : search_in_file({'file_name': 'agent_tools.py', 'pattern': 'completion'})
...

--- Step 5 ---
Action : finish({'answer': 'Found completion() calls in 8 files: ...'})
  TASK COMPLETE
```

### Example 3: Shell Command Usage

```bash
--- Step 3 ---
Thought: Let me count lines across all Python files to get a sense of project size.
Action : shell_command({'command': 'wc -l *.py'})
Observation:   67 main.py
              172 agent_tools.py
              290 agent_react.py
              ...
             2847 total
```

## 🧠 How the Parser Works

The agent produces text in this format:

```
Thought: I need to read the README to understand the project.
Action: read_file(file_name="README.md")
```

The parser uses regex to extract:
1. **Thought**: Everything between `Thought:` and `Action:`
2. **Action**: Function-call style `tool_name(arg1, arg2, ...)`
3. **Arguments**: Supports keyword (`key="value"`), positional, and JSON styles

### Parsing Fallbacks

| Argument Style | Example | Supported? |
|---------------|---------|-----------|
| Keyword | `read_file(file_name="test.py")` | ✅ Yes |
| Positional | `read_file("test.py")` | ✅ Yes |
| JSON | `read_file({"file_name": "test.py"})` | ✅ Yes |
| No args | `list_files()` | ✅ Yes |

## ⚙️ Configuration

### Environment Variables

```env
GEMINI_API_KEY=your-key
OPENAI_API_KEY=your-key
DEFAULT_MODEL=gemini/gemini-1.5-flash
DEFAULT_MAX_ITERATIONS=15
DEFAULT_MAX_TOKENS=2048
```

### CLI Options

```bash
--task "Your task"          # Task description
--model MODEL_NAME          # LLM model to use
--max-iterations N          # Max reasoning steps (default: 15)
--verbose                   # Show full LLM responses
```

## 🔍 Comparison with Other Agents

| Feature | agent_tools.py | function_calling.py | **agent_react.py** |
|---------|---------------|--------------------|--------------------|
| **Reasoning** | Optional (in prompt) | Hidden (internal) | ✅ Forced (Thought) |
| **Action format** | Custom JSON blocks | Native tool_calls | Text Thought/Action |
| **Transparency** | Low | Low | ✅ High |
| **Error recovery** | Basic retry | Basic retry | ✅ Reason about error |
| **Shell access** | ❌ No | ❌ No | ✅ Yes (read-only) |
| **Regex search** | ❌ No | ❌ No | ✅ Yes |

## 💰 Cost Considerations

ReAct typically uses 3-8 iterations per task:

- **Gemini Flash**: Free (up to 15 RPM)
- **GPT-3.5-turbo**: ~$0.005-0.015
- **GPT-4**: ~$0.15-0.40

Higher max_tokens (2048 default) means slightly higher cost per call but better reasoning quality.

## 🐛 Troubleshooting

### Agent doesn't follow Thought/Action format

**Solution**: Try a more capable model (GPT-4, Gemini Pro). Smaller models may not follow structured output reliably.

### "Unknown tool" errors

**Cause**: LLM invented a tool name that doesn't exist.
**Solution**: The observation tells the LLM valid tool names; it self-corrects on the next step.

### Shell command rejected

**Cause**: Command doesn't start with an allowed prefix.
**Solution**: Only read-only commands are allowed for safety. Edit `ALLOWED_PREFIXES` to add more.

### Parser can't extract action

**Cause**: LLM produced non-standard format.
**Solution**: Use `--verbose` to see raw output. The parser handles multiple formats as fallbacks.

## 📚 Learning Path

After mastering this agent:

1. **Add more tools**: Database queries, web requests, code execution
2. **Implement ReAct + Plan**: Combine planning with step-by-step reasoning
3. **Add self-reflection**: Agent evaluates its own reasoning quality
4. **Build ReWOO**: ReAct Without Observation variant (plan all actions first)
5. **Compare with Plan-and-Execute**: Try `agent_planner.py` for structured planning

## 📖 Further Reading

- [ReAct Paper (2022)](https://arxiv.org/abs/2210.03629) - The original research
- [LangChain ReAct Agent](https://python.langchain.com/docs/modules/agents/agent_types/react) - Framework implementation
- [Reflexion Paper](https://arxiv.org/abs/2303.11366) - Self-reflective agents
- [LiteLLM Documentation](https://docs.litellm.ai/)
