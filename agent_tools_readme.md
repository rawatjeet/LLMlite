# AI Agent with Tool Calling

An autonomous AI agent that can complete tasks by deciding which tools to use and when. This demonstrates core concepts of agentic AI systems including tool calling, autonomous decision-making, and multi-step reasoning.

## Files Covered

| File | Lines | Description |
| ---- | ----- | ----------- |
| **agent_tools.py** | 172 | Original. Custom JSON action parsing from markdown code blocks (\`\`\`action blocks). Uses `extract_markdown_block()` and `parse_action()`. Has `list_files`, `read_file`, `terminate` tools. System prompt defines tools as JSON in the prompt text. Agent loop with `while iterations < max_iterations`. Flat script structure. Defaults to `openai/gpt-4o` for generation. |
| **agent_tools_improved.py** | 678 | Improved. Adds `write_file` and `search_files` tools. Adds `safe_json_parse()`. Has `get_system_prompt()` that dynamically injects tool schemas. Proper `run_agent()` function. `execute_tool()` with error handling. Structured CLI with `--task`, `--model`, `--max-iterations`, `--verbose`. `validate_api_key()`. Uses `pathlib.Path` for file operations. File size validation (10 MB limit). Defaults to `gemini/gemini-1.5-flash`. |

## Key Architectural Distinction: Custom vs Native Tool Calling

**Important:** Both `agent_tools.py` and `agent_tools_improved.py` use **CUSTOM JSON parsing** — they instruct the LLM to output tool calls inside markdown \`\`\`action blocks, then parse that text to extract and execute tools. This contrasts with **agent_loop_with_function_calling.py**, which uses **NATIVE function calling** — the LLM API's built-in tool/function-calling feature where the model returns structured tool calls that the API exposes directly. If you want native API-level function calling, see `agent_loop_with_function_calling.py`.

## Original vs Improved Comparison

| Aspect | agent_tools.py (Original) | agent_tools_improved.py (Improved) |
| ------ | ------------------------- | ----------------------------------- |
| **Tool calling** | Custom JSON parsing (\`\`\`action blocks) | Custom JSON parsing (\`\`\`action blocks) |
| **Tools** | `list_files`, `read_file`, `terminate` | + `write_file`, `search_files` |
| **JSON parsing** | `json.loads()` in `parse_action()` | `safe_json_parse()` with error handling |
| **System prompt** | Static JSON in prompt text | `get_system_prompt()` dynamically injects schemas |
| **Structure** | Flat script, inline loop | `run_agent()` function, `execute_tool()` |
| **CLI** | Interactive only (`input()`) | `--task`, `--model`, `--max-iterations`, `--verbose` |
| **API key** | Fails if missing | `validate_api_key()` with clear message |
| **File ops** | `os.listdir`, `open()` | `pathlib.Path`, 10 MB size limit |
| **Default model** | `openai/gpt-4o` | `gemini/gemini-1.5-flash` |

## 🎯 What Makes This a "True Agent"?

Unlike simple scripts or even quasi-agents with fixed workflows, this agent:

✅ **Makes decisions autonomously** - Chooses which tool to use based on the task  
✅ **Adapts its strategy** - Changes approach based on intermediate results  
✅ **Maintains memory** - Remembers what it's done and builds on it  
✅ **Loops until completion** - Continues working until the task is done  
✅ **Uses real tools** - Executes actual Python functions to interact with the system

## 🌟 Features

- **Autonomous Tool Selection**: Agent decides which tools to use
- **Multi-Step Reasoning**: Breaks complex tasks into steps
- **File System Operations**: List, read, write, and search files
- **Conversation Memory**: Maintains context across all steps
- **Error Handling**: Gracefully handles failures and edge cases
- **Configurable Limits**: Set maximum iterations to prevent runaway loops
- **Verbose Mode**: See detailed agent reasoning and decisions

## 🛠️ Available Tools

The agent can use these tools to complete tasks:

| Tool | Description | Example Use |
| --------- | --------------- | --------------------------- |
| `list_files` | Lists files in a directory | "What files are here?" |
| `read_file` | Reads file contents | "Read README.md" |
| `write_file` | Writes to a file | "Create a summary file" |
| `search_files` | Finds files by pattern | "Find all Python files" |
| `terminate` | Ends task with summary | Automatically used when done |

*Note: `write_file` and `search_files` are available in `agent_tools_improved.py` only. The original `agent_tools.py` has `list_files`, `read_file`, and `terminate`.*

## 📋 Prerequisites

- **Python 3.8 or higher**
- **API Key**: Gemini (recommended) or OpenAI
- Basic understanding of Python and command line

## 🚀 Installation

### Step 1: Set Up Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies

Create `requirements.txt`:

```txt
litellm>=1.0.0
python-dotenv>=1.0.0
```

Install:

```bash
pip install -r requirements.txt
```

### Step 3: Configure API Key

Create `.env` file:

```env
# Recommended: Use Gemini (free tier available)
GEMINI_API_KEY=your-gemini-api-key-here

# Or use OpenAI
# OPENAI_API_KEY=your-openai-api-key-here

# Optional: Customize settings
DEFAULT_MODEL=gemini/gemini-1.5-flash
DEFAULT_MAX_ITERATIONS=10
DEFAULT_MAX_TOKENS=1024
```

### Step 4: Add to .gitignore

```bash
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
```

## 💻 Usage

### Interactive Mode

Run without arguments and follow prompts:

```bash
python agent_tools.py
```

Or with the improved version:

```bash
python agent_tools_improved.py
```

**Example interaction:**

```bash
What would you like me to do?
Your task: Find all Python files and tell me how many there are

🔄 Iteration 1/10
💭 Reasoning: I need to search for Python files in the directory...
🔧 Action: search_files
✅ Result: 5 items

🔄 Iteration 2/10
💭 Reasoning: Now I'll count and summarize...
🔧 Action: terminate
✅ TASK COMPLETED
📊 Summary: I found 5 Python files in this directory: main.py, agent_tools.py, quasi-agent.py, test_main.py, and utils.py
```

### Command-Line Mode

Provide the task directly (improved version):

```bash
python agent_tools_improved.py --task "What Python files are in this directory?"
```

### Options

```bash
# Verbose mode (see full reasoning)
python agent_tools_improved.py --verbose

# Custom model
python agent_tools_improved.py --model openai/gpt-4

# Limit iterations (prevent long loops)
python agent_tools_improved.py --max-iterations 5

# Combine options
python agent_tools_improved.py --task "Read all .md files" --verbose --max-iterations 15
```

## 📝 Example Tasks

### Simple File Operations

```bash
# List all files
python agent_tools_improved.py --task "What files are in this directory?"

# Read a specific file
python agent_tools_improved.py --task "Read the README.md file"

# Find specific files
python agent_tools_improved.py --task "Find all test files"
```

### Complex Multi-Step Tasks

```bash
# Analyze project structure
python agent_tools_improved.py --task "List all Python files and tell me what each one does based on its name"

# Content analysis
python agent_tools_improved.py --task "Read all .py files and tell me which ones have the word 'agent' in them"

# File creation
python agent_tools_improved.py --task "Create a file called summary.txt with a list of all Python files"
```

### Research Tasks

```bash
# Project overview
python agent_tools_improved.py --task "Read the README and summarize what this project does"

# Code inventory
python agent_tools_improved.py --task "Find all Python files, read them, and create a summary of the project structure"
```

## 🧠 How the Agent Works

### The Agent Loop

```bash
┌─────────────────────────────────────────┐
│  1. User provides task                  │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  2. Agent thinks about what to do       │
│     "I need to list files first..."     │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  3. Agent chooses a tool                │
│     tool_name: "list_files"             │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  4. Tool executes (Python function)     │
│     result: ["file1.py", "file2.py"]    │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  5. Result added to memory              │
│     Agent remembers what happened       │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  6. Loop back to step 2                 │
│     (unless task complete)              │
└─────────────────────────────────────────┘
```

### Memory Management

The agent maintains conversation history:

```python
memory = [
    {"role": "system", "content": "You are an AI agent..."},
    {"role": "user", "content": "Find Python files"},
    {"role": "assistant", "content": "I'll search for *.py files..."},
    {"role": "user", "content": '{"result": ["main.py", "test.py"]}'},
    {"role": "assistant", "content": "I found 2 files..."},
    # ... continues until termination
]
```

Each step builds on previous knowledge!

### Tool Execution Flow (Custom JSON Parsing)

Both `agent_tools.py` and `agent_tools_improved.py` use custom parsing of ```action blocks:

```python
# 1. Agent generates response with action
response = """
I need to list the files first to see what's available.

```action
{
    "tool_name": "list_files",
    "args": {}
}
```

"""

# 2. Parse the action
action = parse_action(response)
# → {"tool_name": "list_files", "args": {}}

# 3. Execute the tool
result = execute_tool("list_files", {})
# → {"result": ["file1.py", "file2.py", "README.md"]}

# 4. Add to memory for next iteration
memory.append({"role": "user", "content": json.dumps(result)})
```

*Contrast: `agent_loop_with_function_calling.py` uses native API function calling — the LLM returns structured tool calls directly, no markdown parsing needed.*

## 🎓 Key Concepts Explained

### 1. Autonomous Decision Making

**Traditional Script:**
```python
# Fixed sequence
step1()
step2()
step3()
```

**Agent:**

```python
# Agent decides at each step
while not done:
    action = agent.decide_next_action()  # AI chooses!
    result = execute(action)
    if should_terminate(result):
        done = True
```

### 2. Tool Calling

The agent doesn't just generate text—it can execute real Python functions:

```python
# Agent decides to use this tool
{
    "tool_name": "read_file",
    "args": {"file_name": "data.txt"}
}

# Python executes the actual function
def read_file(file_name: str) -> str:
    with open(file_name) as f:
        return f.read()
```

### 3. Iterative Refinement

The agent can try different approaches:

```bash
Iteration 1: List files → Found 10 files
Iteration 2: Filter for .py → Found 3 Python files
Iteration 3: Read first file → Got contents
Iteration 4: Terminate with summary
```

### 4. Error Recovery

If something goes wrong, the agent adapts:

```bash
Iteration 1: Read "config.txt" → Error: File not found
Iteration 2: List files to find it → Found "config.json"
Iteration 3: Read "config.json" → Success!
```

## ⚙️ Configuration

### Environment Variables

```env
# Model Selection
DEFAULT_MODEL=gemini/gemini-1.5-flash
# Options: gemini/gemini-1.5-flash, gemini/gemini-1.5-pro, openai/gpt-4

# Agent Limits
DEFAULT_MAX_ITERATIONS=10    # Prevent infinite loops
DEFAULT_MAX_TOKENS=1024      # Max response length
```

### Adding New Tools

Easy to extend with custom tools:

```python
def calculate_stats(file_name: str) -> Dict:
    """Calculate statistics about a file."""
    content = read_file(file_name)
    return {
        "lines": len(content.split('\n')),
        "words": len(content.split()),
        "chars": len(content)
    }

# Add to registry
TOOLS["calculate_stats"] = calculate_stats

# Add to schemas
TOOL_SCHEMAS["calculate_stats"] = {
    "description": "Calculates statistics for a file",
    "parameters": {
        "file_name": {
            "type": "string",
            "description": "File to analyze"
        }
    }
}
```

Now the agent can use your custom tool!

## 🐛 Troubleshooting

### Agent loops without completing

**Solution**: Reduce max iterations or improve system prompt:

```bash
python agent_tools_improved.py --max-iterations 5
```

### Agent can't find files

**Solution**: Use verbose mode to see what's happening:

```bash
python agent_tools_improved.py --verbose
```

### Invalid tool calls

**Cause**: LLM not following format correctly

**Solution**:

1. Try a different model (GPT-4 is more reliable)
2. Check system prompt formatting
3. Use verbose mode to see raw responses

### "Maximum iterations reached"

**Cause**: Task is too complex or agent is stuck

**Solutions**:

1. Break task into smaller parts
2. Increase `--max-iterations`
3. Be more specific in task description
4. Check if agent is confused (use `--verbose`)

## 💰 Cost Considerations

### API Call Estimates

Per task completion (average 3-5 iterations):

- **Gemini Flash**: Free (up to 15 RPM)
- **GPT-3.5-turbo**: ~$0.005-0.01
- **GPT-4**: ~$0.15-0.25

### Reducing Costs

1. **Use iteration limits** - Prevent expensive runaway loops
2. **Choose efficient models** - Gemini Flash is free
3. **Be specific** - Clear tasks need fewer iterations
4. **Monitor usage** - Check API dashboards regularly

## 🔒 Security Considerations

### File System Access

The agent can read/write files in the current directory:

⚠️ **Be careful with:**

- Sensitive files in the working directory
- Write operations (agent can overwrite files)
- Running with elevated privileges

✅ **Best practices:**

- Run in an isolated directory
- Review generated files before using
- Don't give access to system files
- Use read-only mode if just analyzing

### API Key Security

```env
# Good: In .env file
GEMINI_API_KEY=your-key

# Bad: In code
api_key = "your-key-here"  # DON'T DO THIS
```

## 📊 Comparison with Other Agent Types

| Feature | Script | Quasi-Agent | Tool Agent (This) |
| --------- | -------- | ------------- | ------------------- |
| Decision Making | ❌ Fixed | ❌ Fixed workflow | ✅ Autonomous |
| Tool Use | ❌ No | ❌ No | ✅ Yes |
| Adaptability | ❌ None | ❌ Limited | ✅ High |
| Memory | ❌ No | ✅ Yes | ✅ Yes |
| Iteration | ❌ No | ❌ No | ✅ Yes |
| Complexity | Low | Medium | High |

## 🚀 Advanced Usage

### Custom System Prompts

Modify agent behavior:

```python
system_prompt = """You are a careful AI agent that:
- Always lists files before reading
- Asks for confirmation before writing
- Provides detailed explanations
..."""
```

### Tool Chaining

Agent automatically chains tools:

```bash
Task: "Summarize all Python files"

Step 1: search_files("*.py") → [file1.py, file2.py]
Step 2: read_file("file1.py") → "content..."
Step 3: read_file("file2.py") → "content..."
Step 4: terminate(summary of both)
```

### Integration with Other Systems

```python
from agent_tools_improved import run_agent

# Use in your application
result = run_agent(
    task="Find project documentation",
    max_iterations=5,
    verbose=False
)
print(result)
```

## 📚 Learning Path

After mastering this agent:

1. **Add more tools** - Database access, API calls, etc.
2. **Implement planning** - Agent creates plan before executing
3. **Add memory persistence** - Save state between runs
4. **Multi-agent systems** - Multiple agents collaborating
5. **Reinforcement learning** - Agent learns from experience

## 🤝 Contributing Ideas

Want to extend this agent? Try adding:

- **Git operations** - Commit, push, pull
- **Code analysis** - Lint, format, test
- **Web search** - Find information online
- **Database tools** - Query data
- **API integration** - Call external services

## 📖 Further Reading

- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)
