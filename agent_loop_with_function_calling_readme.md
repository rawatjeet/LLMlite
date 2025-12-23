# Simple Agent with Native Function Calling

A straightforward agent implementation using LLM's native function calling capability. This is the recommended approach for most use cases due to its simplicity and reliability.

## 🎯 What This Demonstrates

This script shows how to build an agent using **native function calling** - a feature built into modern LLMs that lets them directly invoke functions without custom parsing logic.

### Why Native Function Calling?

**Traditional Approach (Custom Parsing):**

```bash
LLM → "Use read_file with name='data.txt'" → Parse JSON → Execute
     ❌ Fragile, requires custom parsing, prone to errors
```

**Native Function Calling (This Script):**

```bash
LLM → [Function Call Object] → Execute
     ✅ Reliable, built-in, standardized
```

## 🌟 Key Features

- **Simple & Clean**: ~200 lines vs 500+ for custom parsing
- **Reliable**: Uses LLM's built-in capability
- **Production-Ready**: Robust error handling
- **Easy to Extend**: Add tools in minutes
- **Standard Protocol**: Works across different LLMs

## 📊 How It Works

### The Agent Loop

```bash
┌─────────────────────────────────────┐
│  1. User provides task              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  2. Send to LLM with tools          │
│     - Conversation history          │
│     - Available tools list          │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  3. LLM returns function call       │
│     {                               │
│       "name": "read_file",          │
│       "args": {"file_name": "x"}    │
│     }                               │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  4. Execute function                │
│     result = read_file("x")         │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  5. Add result to conversation      │
│     and loop back to step 2         │
└─────────────────────────────────────┘
```

### Function Calling Protocol

**Tool Definition:**

```python
{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Reads contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "File to read"
                }
            },
            "required": ["file_name"]
        }
    }
}
```

**LLM Response:**

```python
response.choices[0].message.tool_calls[0]
# → ToolCall(
#     function=Function(
#         name="read_file",
#         arguments='{"file_name": "data.txt"}'
#     )
# )
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install litellm python-dotenv

# Configure API key
echo "GEMINI_API_KEY=your-key-here" > .env
```

### Basic Usage

```bash
# Interactive mode
python agent_loop_with_function_calling.py

# Direct task
python agent_loop_with_function_calling.py --task "List all Python files"

# Verbose output
python agent_loop_with_function_calling.py --verbose

# Custom model
python agent_loop_with_function_calling.py --model openai/gpt-4
```

## 🛠️ Available Tools

| Tool | Description | Example |
| ------ | ------------- | --------- |
| `list_files` | List files in directory | `list_files(directory=".")` |
| `read_file` | Read file contents | `read_file(file_name="data.txt")` |
| `search_files` | Find files by pattern | `search_files(pattern="*.py")` |
| `terminate` | End with summary | `terminate(message="Done")` |

## 📝 Example Sessions

### Example 1: Find Python Files

```bash
Task: "What Python files are in this directory?"

Iteration 1:
  Tool: search_files
  Args: pattern="*.py"
  Result: ["main.py", "agent.py", "test.py"]

Iteration 2:
  Tool: terminate
  Args: message="Found 3 Python files: main.py, agent.py, test.py"
  ✅ COMPLETED
```

### Example 2: Read and Analyze

```bash
Task: "Read the README and tell me what this project does"

Iteration 1:
  Tool: list_files
  Args: directory="."
  Result: ["README.md", "main.py", ...]

Iteration 2:
  Tool: read_file
  Args: file_name="README.md"
  Result: "# My Project\nThis is a..."

Iteration 3:
  Tool: terminate
  Args: message="This project is a Python library for..."
  ✅ COMPLETED
```

## 🔧 Adding Custom Tools

### Step 1: Create the Function

```python
def count_lines(file_name: str) -> int:
    """Count lines in a file."""
    with open(file_name) as f:
        return len(f.readlines())
```

### Step 2: Add to Registry

```python
TOOL_FUNCTIONS["count_lines"] = count_lines
```

### Step 3: Define Tool Schema

```python
TOOLS.append({
    "type": "function",
    "function": {
        "name": "count_lines",
        "description": "Counts the number of lines in a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "Path to the file"
                }
            },
            "required": ["file_name"]
        }
    }
})
```

That's it! The agent can now count lines.

## 🎓 Key Concepts

### 1. Native vs Custom Function Calling

**Custom Parsing (❌ Complex):**

```python
# Agent must output specific JSON format
response = llm.generate(prompt)
# → "I'll use read_file: ```json\n{\"tool\": \"read_file\"...}```"
json_str = extract_code_block(response)
action = json.loads(json_str)  # Hope this works!
```

**Native Calling (✅ Simple):**

```python
# LLM handles it internally
response = completion(messages=messages, tools=tools)
if response.tool_calls:
    tool = response.tool_calls[0]  # Clean, standardized
    # No parsing needed!
```

### 2. Tool Schemas

The schema tells the LLM:

- What the tool does
- What parameters it needs
- What types they are
- Which are required

```python
{
    "name": "search_files",          # Tool identifier
    "description": "Searches...",    # What it does
    "parameters": {                  # What it needs
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",    # Type info
                "description": "..." # Parameter help
            }
        },
        "required": ["pattern"]      # Must provide
    }
}
```

### 3. Conversation Memory

Each iteration adds to the conversation:

```python
memory = [
    {"role": "system", "content": "You are an agent..."},
    {"role": "user", "content": "Find Python files"},
    {"role": "assistant", "content": '{"tool_name": "search_files"...}'},
    {"role": "user", "content": '{"result": ["a.py", "b.py"]}'},
    # ... continues
]
```

The agent sees the full history on each call.

## 🔍 Comparison with Other Approaches

### vs Custom Parsing (agent_tools.py)

| Aspect | Custom Parsing | Native Function Calling |
| -------- | ---------------- | ------------------------- |
| Code Complexity | High (~500 lines) | Low (~200 lines) |
| Reliability | Medium | High |
| Setup Time | Long | Quick |
| Maintenance | Complex | Simple |
| LLM Requirements | Any | Needs function calling support |

### vs Framework (a_sample_agent_framework.py)

| Aspect | Framework | Simple Agent |
| -------- | ----------- | -------------- |
| Architecture | GAME (complex) | Loop (simple) |
| Modularity | High | Medium |
| Learning Curve | Steep | Gentle |
| Use Case | Large projects | Quick tasks |
| Lines of Code | 800+ | 200 |

## ⚙️ Configuration

### Environment Variables

```env
DEFAULT_MODEL=gemini/gemini-1.5-flash
DEFAULT_MAX_ITERATIONS=10
GEMINI_API_KEY=your-key
OPENAI_API_KEY=your-key  # Alternative
```

### Command-Line Options

```bash
--task "Your task"         # Task to complete
--model MODEL_NAME         # LLM to use
--max-iterations N         # Iteration limit
--verbose                  # Detailed output
```

## 🐛 Troubleshooting

### "No tool calls in response"

**Cause**: LLM returned text instead of function call

**Solution**:

1. Check system prompt clarity
2. Ensure model supports function calling
3. Verify tool descriptions are clear

### "Invalid arguments"

**Cause**: LLM provided wrong parameter types

**Solution**:

1. Make parameter descriptions more specific
2. Add examples in tool description
3. Add validation in tool function

### "Maximum iterations reached"

**Cause**: Agent didn't terminate

**Solution**:

1. Make terminate condition clearer in system prompt
2. Increase max iterations
3. Check if agent is stuck in a loop (use --verbose)

## 💰 Cost Considerations

### Per Task Estimate

Average task with 3-5 tool calls:

- **Gemini Flash**: Free (up to 15 RPM)
- **GPT-3.5-turbo**: $0.002-0.005
- **GPT-4**: $0.06-0.10

### Cost Optimization

1. **Use efficient models**: Gemini Flash is free
2. **Limit iterations**: Set reasonable max
3. **Clear instructions**: Reduce iterations needed
4. **Batch operations**: Combine related tasks

## 🎯 Use Cases

### Perfect For

✅ **File operations**

- Listing, reading, searching files
- Code analysis
- Log file processing

✅ **Simple automation**

- Report generation
- Data extraction
- Content summarization

✅ **Research tasks**

- Finding information
- Analyzing documents
- Creating summaries

### Not Ideal For

❌ **Complex multi-agent workflows**
→ Use agent_framework.py instead

❌ **Tasks requiring planning**
→ Add planning phase first

❌ **Long-running processes**
→ Add checkpointing/persistence

## 🚀 Advanced Patterns

### Pattern 1: Confirmation Required

```python
def delete_file(file_name: str) -> str:
    """Delete a file (dangerous operation)."""
    response = input(f"Delete {file_name}? (y/n): ")
    if response.lower() == 'y':
        os.remove(file_name)
        return f"Deleted {file_name}"
    return "Cancelled"
```

### Pattern 2: Streaming Results

```python
def read_large_file(file_name: str) -> str:
    """Read large file in chunks."""
    result = []
    with open(file_name) as f:
        for i, line in enumerate(f):
            if i < 100:  # First 100 lines
                result.append(line)
            else:
                break
    return "".join(result) + "\n... (truncated)"
```

### Pattern 3: Chained Tools

Agent automatically chains tools:

```python
Task: "Summarize all Python files"
  → search_files("*.py")
  → read_file("file1.py")
  → read_file("file2.py")
  → terminate(summary)
```

## 🔒 Security

### File Access

```python
def read_file(file_name: str) -> str:
    # Validate path
    if ".." in file_name or file_name.startswith("/"):
        return "Error: Invalid path"
    
    # Limit to current directory
    if not Path(file_name).resolve().is_relative_to(Path.cwd()):
        return "Error: Access denied"
    
    # ... safe read
```

### Size Limits

```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def read_file(file_name: str) -> str:
    size = Path(file_name).stat().st_size
    if size > MAX_FILE_SIZE:
        return f"Error: File too large ({size/1024/1024:.1f}MB)"
    # ... read file
```

## 📊 Performance Tips

1. **Limit memory**: Keep conversation history reasonable
2. **Clear descriptions**: Help LLM choose correct tool
3. **Efficient tools**: Optimize tool implementations
4. **Early termination**: Exit when task complete

## 🎓 Learning Path

1. **Run examples**: Try different tasks
2. **Add a tool**: Implement custom function
3. **Modify system prompt**: Change agent behavior
4. **Handle errors**: Add retry logic
5. **Optimize**: Reduce iterations needed

## 📚 Further Reading

- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)
- [LiteLLM Documentation](https://docs.litellm.ai/)

## 🤝 When to Use This vs Other Approaches

**Use This When:**

- You need simple, reliable tool calling
- Task is straightforward
- You want minimal code
- You're building a proof of concept

**Use agent_framework.py When:**

- You need modular, extensible architecture
- Building a large system
- Multiple goal types
- Production deployment

**Use agent_tools.py When:**

- Need custom parsing logic
- LLM doesn't support function calling
- Very specific requirements
