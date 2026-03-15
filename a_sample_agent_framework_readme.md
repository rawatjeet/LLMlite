# Advanced Agent Framework (GAME Architecture)

A production-ready framework for building sophisticated AI agents using the GAME architecture: **G**oals, **A**ctions, **M**emory, **E**nvironment.

## Files Covered

| File | Lines | Description |
|------|-------|-------------|
| **a_sample_agent_framework.py** | 413 | Original implementation. Introduces GAME architecture with hardcoded goals, fixed user input, and `openai/gpt-4o`. |
| **a_sample_agent_framework_improved.py** | 907 | Improved version. Adds CLI, configurable model, factory function, and enhanced Memory/ActionRegistry APIs. |
| **tool_decorators.py** | 593 | Extension. Combines GAME with `@register_tool` decorator, auto-generated JSON schemas, and `PythonActionRegistry` with tag-based filtering. |

---

## 🎯 What is GAME Architecture?

GAME is a structured approach to building AI agents:

- **Goals (G)**: What the agent should accomplish
- **Actions (A)**: What the agent can do (its capabilities)
- **Memory (M)**: What the agent remembers (conversation history)
- **Environment (E)**: Where the agent operates (execution context)

This architecture separates concerns and makes agents modular, testable, and extensible.

## 🌟 Key Features

- **Modular Design**: Each component (Goals, Actions, Memory, Environment) is independent
- **Function Calling**: Uses native LLM function calling (not custom parsing)
- **Type Safety**: Full type hints and dataclasses
- **Error Handling**: Comprehensive error handling and recovery
- **Extensible**: Easy to add new actions and goals
- **Production-Ready**: Includes logging, error tracking, and resource management

## 📊 Architecture Overview

```bash
┌─────────────────────────────────────────────────────┐
│                      AGENT                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐            │
│  │  GOALS   │  │  MEMORY  │  │ ACTIONS │            │
│  │          │  │          │  │         │            │
│  │ Priority │  │ History  │  │ Registry│            │
│  │ Ordered  │  │ Context  │  │ Tools   │            │
│  └──────────┘  └──────────┘  └─────────┘            │
│       │             │              │                │
│       └─────────────┼──────────────┘                │
│                     │                               │
│              ┌──────▼──────┐                        │
│              │   PROMPT    │                        │
│              │ CONSTRUCTOR │                        │
│              └──────┬──────┘                        │
│                     │                               │
│              ┌──────▼──────┐                        │
│              │     LLM     │                        │
│              └──────┬──────┘                        │
│                     │                               │
│              ┌──────▼──────┐                        │
│              │   PARSER    │                        │
│              └──────┬──────┘                        │
│                     │                               │
│       ┌─────────────┴──────────────┐                │
│       │                            │                │
│  ┌────▼────────┐            ┌──────▼──────┐         │
│  │ ENVIRONMENT │            │   MEMORY    │         │
│  │  (Execute)  │────────────│  (Update)   │         │
│  └─────────────┘            └─────────────┘         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Original vs Improved: Key Differences

| Aspect | Original (`a_sample_agent_framework.py`) | Improved (`a_sample_agent_framework_improved.py`) |
|--------|------------------------------------------|--------------------------------------------------|
| **Language class** | `AgentFunctionCallingActionLanguage` | `AgentFunctionCallingLanguage` (renamed) |
| **Action** | No `requires_confirmation` | Adds `requires_confirmation` for user approval |
| **Memory** | `get_memories(limit)` only | Adds `get_recent_memories(count)`, `clear()`, `__len__()` |
| **ActionRegistry** | `register`, `get_action`, `get_actions` | Adds `list_action_names()` |
| **generate_response** | Hardcoded `openai/gpt-4o`, no model param | `generate_response(prompt, model)` with configurable model |
| **Default model** | `openai/gpt-4o` | `gemini/gemini-1.5-flash` |
| **Entry point** | Non-interactive, fixed `user_input` | Full CLI: `--task`, `--max-iterations`, `--verbose` |
| **Agent creation** | Inline setup | `create_file_agent()` factory function |
| **Error handling** | Basic | `TypeError` vs generic `Exception`, verbose tracebacks |
| **Output** | Minimal prints | Rich progress output, iteration counts, final statistics |

---

## tool_decorators.py and the @register_tool Pattern

`tool_decorators.py` extends the GAME framework by combining it with a decorator-based tool registration system. Instead of manually creating `Action` objects and registering them, you decorate functions with `@register_tool`.

### @register_tool Decorator

```python
@register_tool(tags=["file_operations", "read"])
def read_project_file(name: str) -> str:
    """Reads and returns the content of a specified project file."""
    with open(name, "r") as f:
        return f.read()

@register_tool(tags=["system"], terminal=True)
def terminate(message: str) -> str:
    """Terminates the agent's execution with a final message."""
    return f"{message}\nTerminating..."
```

**Decorator parameters:**

- `tool_name` — Override the tool name (default: function name)
- `description` — Override description (default: docstring)
- `parameters_override` — Override JSON schema (default: auto-generated)
- `terminal` — Whether this action ends the agent loop
- `tags` — List of tags for filtering (e.g., `["file_operations", "read"]`)

### get_tool_metadata() and Auto-Generated Schemas

`get_tool_metadata()` automatically derives JSON schemas from Python type hints and docstrings:

- **Type hints** → JSON schema types (`str` → `"string"`, `int` → `"integer"`, etc.)
- **Docstring** → Tool description
- **Parameters without defaults** → `required` array
- Skips special params like `action_context`, `action_agent`

### to_openai_tools() Converter

Converts tool metadata to OpenAI-compatible function calling format:

```python
openai_tools = to_openai_tools(tools_metadata)
```

---

## PythonActionRegistry and Tag-Based Filtering

`PythonActionRegistry` extends `ActionRegistry` to auto-load decorated tools from the global `tools` dictionary, with optional filtering by tags or tool names.

### How It Works

1. **Global registry**: `@register_tool` populates `tools` and `tools_by_tag` dictionaries at import time.
2. **Filtering**: `PythonActionRegistry` accepts `tags` and/or `tool_names` to include only matching tools.
3. **Terminate tool**: The terminate tool is tracked separately and can be registered via `register_terminate_tool()`.

### Constructor

```python
PythonActionRegistry(tags=None, tool_names=None)
```

- **tags** — Include only tools that have *any* of these tags
- **tool_names** — Include only tools whose names are in this list

### Examples

```python
# Load all file_operations and system tools
action_registry = PythonActionRegistry(tags=["file_operations", "system"])

# Load only specific tools by name
action_registry = PythonActionRegistry(tool_names=["read_project_file", "list_project_files", "terminate"])

# Load all registered tools (no filter)
action_registry = PythonActionRegistry()
```

### Tag Matching Logic

A tool is included if:

- `tags` is `None` **or** the tool has at least one tag in `tags`
- **and** `tool_names` is `None` **or** the tool name is in `tool_names`

---

## 🔍 Core Components Explained

### 1. Goals

Goals define what the agent should accomplish. They have:

- **Priority**: Higher priority goals are shown first
- **Name**: Short identifier
- **Description**: Detailed instructions

```python
Goal(
    priority=1,
    name="Read Files",
    description="Read all Python files in the project directory"
)
```

### 2. Actions

Actions are capabilities - functions the agent can execute:

```python
Action(
    name="read_file",
    function=read_file_impl,
    description="Reads a file from disk",
    parameters={
        "type": "object",
        "properties": {
            "filename": {"type": "string"}
        },
        "required": ["filename"]
    },
    terminal=False  # Doesn't end the agent loop
)
```

**Key attributes:**

- `terminal`: If True, this action ends the agent loop
- `requires_confirmation`: If True, asks before executing

### 3. Memory

Memory stores the conversation history:

```python
memory = Memory()
memory.add_memory({"type": "user", "content": "Read config.json"})
memory.add_memory({"type": "assistant", "content": "I'll read that file"})
memory.add_memory({"type": "environment", "content": '{"status": "success"}'})
```

**Memory types:**

- `user`: User messages
- `assistant`: Agent decisions
- `environment`: Execution results
- `system`: System instructions

### 4. Environment

Environment executes actions safely:

```python
environment = Environment()
result = environment.execute_action(action, {"filename": "data.txt"})
# Returns: {"tool_executed": True, "result": "file contents..."}
```

### 5. Agent Language

Defines how the agent communicates:

```python
# Using function calling
language = AgentFunctionCallingLanguage()

# Constructs prompts
prompt = language.construct_prompt(actions, environment, goals, memory)

# Parses responses
action_dict = language.parse_response(llm_response)
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install litellm python-dotenv

# Set up API key
echo "GEMINI_API_KEY=your-key-here" > .env
```

### Basic Usage

```python
from agent_framework import Agent, Goal, Action, ActionRegistry, Environment
from agent_framework import AgentFunctionCallingLanguage, generate_response

# Define goals
goals = [
    Goal(priority=1, name="Task", description="Complete the user's task")
]

# Create actions
action_registry = ActionRegistry()
action_registry.register(Action(
    name="my_action",
    function=lambda x: f"Processed: {x}",
    description="Does something useful",
    parameters={"type": "object", "properties": {"x": {"type": "string"}}}
))

# Create agent
agent = Agent(
    goals=goals,
    agent_language=AgentFunctionCallingLanguage(),
    action_registry=action_registry,
    generate_response_fn=generate_response,
    environment=Environment()
)

# Run agent
memory = agent.run("Do something useful")
```

### Using tool_decorators (Decorator Pattern)

```python
from tool_decorators import (
    Agent, Goal, Environment, AgentFunctionCallingActionLanguage,
    PythonActionRegistry, generate_response, register_tool
)

@register_tool(tags=["file_operations"])
def my_tool(param: str) -> str:
    """Does something useful."""
    return f"Processed: {param}"

agent = Agent(
    goals=[Goal(priority=1, name="Task", description="Complete the task")],
    agent_language=AgentFunctionCallingActionLanguage(),
    action_registry=PythonActionRegistry(tags=["file_operations", "system"]),
    generate_response=generate_response,
    environment=Environment()
)
memory = agent.run("Do something useful")
```

## 📝 Example: File Analysis Agent

The included example creates an agent that can:

1. List Python files
2. Read file contents
3. Generate documentation

```bash
# Original (fixed task)
python a_sample_agent_framework.py

# Improved (CLI)
python a_sample_agent_framework_improved.py --task "Analyze Python files" --verbose

# With decorators
python tool_decorators.py
```

## 🎓 Understanding the GAME Loop

```python
while not done:
    # 1. GOALS + ACTIONS + MEMORY → PROMPT
    prompt = construct_prompt(goals, actions, memory)
    
    # 2. PROMPT → LLM → RESPONSE
    response = llm.generate(prompt)
    
    # 3. RESPONSE → ACTION
    action = parse_response(response)
    
    # 4. ACTION → ENVIRONMENT → RESULT
    result = environment.execute(action)
    
    # 5. RESULT → MEMORY
    memory.add(response, result)
    
    # 6. Check if done
    if action.terminal:
        done = True
```

## 🔧 Adding Custom Actions

### Step 1: Define the Function

```python
def search_files(pattern: str, directory: str = ".") -> List[str]:
    """Search for files matching a pattern."""
    from pathlib import Path
    return [str(p) for p in Path(directory).glob(pattern)]
```

### Step 2: Create Action

```python
search_action = Action(
    name="search_files",
    function=search_files,
    description="Searches for files matching a glob pattern",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern (e.g., '*.py')"
            },
            "directory": {
                "type": "string",
                "description": "Directory to search (default: current)"
            }
        },
        "required": ["pattern"]
    }
)
```

### Step 3: Register

```python
action_registry.register(search_action)
```

**Or with decorator:**

```python
@register_tool(tags=["file_operations"])
def search_files(pattern: str, directory: str = ".") -> List[str]:
    """Search for files matching a pattern."""
    from pathlib import Path
    return [str(p) for p in Path(directory).glob(pattern)]
```

That's it! The agent can now use your custom action.

## 🎯 Design Patterns

### Pattern 1: Terminal Actions

Actions that end the agent loop:

```python
Action(
    name="terminate",
    function=lambda msg: f"Done: {msg}",
    description="Ends the agent loop",
    parameters={...},
    terminal=True  # This ends the loop
)
```

### Pattern 2: Chained Actions

Agent automatically chains actions:

```bash
Task: "Analyze all Python files"
  ↓
1. list_project_files() → ["a.py", "b.py"]
  ↓
2. read_project_file("a.py") → "contents of a..."
  ↓
3. read_project_file("b.py") → "contents of b..."
  ↓
4. terminate(summary) → Done
```

### Pattern 3: Error Recovery

Environment catches errors and returns them to the agent:

```python
result = environment.execute_action(action, args)
if not result["tool_executed"]:
    # Agent sees the error and can try something else
    error = result["error"]
```

## 🔍 Comparison with Other Approaches

| Feature | Custom Parsing | Function Calling (This) |
| --------- | ---------------- | ------------------------- |
| Reliability | ⚠️ Fragile | ✅ Robust |
| Setup | Complex | Simple |
| LLM Support | Any model | Needs function calling |
| Type Safety | Manual | Automatic |
| Error Handling | Custom | Built-in |

## 💡 Advanced Features

### Memory Filtering

```python
# Get recent context only
recent = memory.get_recent_memories(count=5)

# Remove system messages
user_memory = memory.copy_without_system_memories()

# Clear memory
memory.clear()

# Check size
len(memory)
```

### Goal Prioritization

```python
goals = [
    Goal(priority=1, name="Critical", description="Must do first"),
    Goal(priority=2, name="Important", description="Do after critical"),
    Goal(priority=3, name="Optional", description="Do if time permits")
]
# Agent sees them in priority order
```

### Action Registry Management

```python
# List all actions
action_names = action_registry.list_action_names()

# Get specific action
action = action_registry.get_action("read_file")

# Check if action exists
if action_registry.get_action("unknown") is None:
    print("Action not found")
```

## 🐛 Debugging

### Verbose Mode

```bash
python a_sample_agent_framework_improved.py --verbose
```

Shows:

- Full LLM responses
- Complete error tracebacks
- Detailed execution logs

### Memory Inspection

```python
# After running
for item in memory.get_memories():
    print(f"{item['type']}: {item['content'][:100]}...")
```

### Action Testing

```python
# Test action directly
action = action_registry.get_action("read_file")
result = action.execute(name="test.txt")
print(result)
```

## ⚙️ Configuration

### Environment Variables

```env
DEFAULT_MODEL=gemini/gemini-1.5-flash
DEFAULT_MAX_ITERATIONS=50
GEMINI_API_KEY=your-key
```

### Command-Line Options

```bash
--task "Custom task"           # Specify task
--max-iterations 100          # Increase iteration limit
--verbose                     # Detailed output
```

## 🎯 Use Cases

### 1. Code Analysis

```python
goals = [
    Goal(priority=1, name="Analyze", description="Analyze code quality"),
    Goal(priority=2, name="Report", description="Generate report")
]
```

### 2. Data Processing

```python
actions = [
    Action("load_data", load_fn, "Load dataset", ...),
    Action("transform_data", transform_fn, "Transform dataset", ...),
    Action("save_results", save_fn, "Save results", ...)
]
```

### 3. Research Assistant

```python
goals = [
    Goal(priority=1, name="Search", description="Find relevant papers"),
    Goal(priority=2, name="Summarize", description="Create summary")
]
```

## 🔒 Security Considerations

### File Access

Actions can access the file system. Be careful:

```python
def read_file(name: str) -> str:
    # Validate path to prevent directory traversal
    if ".." in name or name.startswith("/"):
        raise ValueError("Invalid path")
    # ... safe read logic
```

### Resource Limits

```python
# Limit iterations to prevent infinite loops
agent.run(task, max_iterations=50)

# Limit memory size
if len(memory) > 1000:
    memory.items = memory.items[-100:]  # Keep last 100
```

## 📊 Performance Tips

1. **Limit memory size**: Keep only recent context
2. **Batch operations**: Combine related actions
3. **Cache results**: Save expensive computations
4. **Use efficient models**: Gemini Flash vs GPT-4

## 🚀 Next Steps

After mastering this framework:

1. **Add new action types**: Database access, API calls
2. **Implement planning**: Agent creates plan before acting
3. **Add learning**: Agent improves from experience
4. **Multi-agent systems**: Multiple agents collaborating
5. **Persistent memory**: Save state between runs

## 📚 Further Reading

- [LiteLLM Function Calling](https://docs.litellm.ai/docs/completion/function_call)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

## 🤝 Contributing

To extend this framework:

1. Subclass `AgentLanguage` for custom protocols
2. Add actions to `ActionRegistry` (or use `@register_tool`)
3. Implement custom `Environment` behavior
4. Create domain-specific `Goal` sets
