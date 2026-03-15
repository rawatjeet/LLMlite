# Enhanced Agent with Batch Operations

An improved agent that extends basic function calling with batch file operations for more efficient task completion. Perfect for tasks that require processing multiple files.

## Files Covered

| File | Lines | Description |
| ---- | ----- | ----------- |
| **agent_loop_with_function_calling2.py** | 252 | Original. Extends the basic agent with `read_all_files()` batch tool and `summarize_file_content()` helper. Has `--mock` and `--task` CLI args. Has commented-out mock mode logic. Has `list_files(path)` with custom path param. Defaults to `openai/gpt-4`. |
| **agent_loop_with_function_calling2_improved.py** | 633 | Improved. Adds `search_files` tool. Has `format_result_summary()` for cleaner output display. `read_all_files()` with `pathlib.Path`, file size checking (10 MB), and error isolation per file. Full CLI with `--task`, `--model`, `--max-iterations`, `--verbose`. Structured `run_agent()`, `execute_tool()`, `validate_api_key()`, `main()`. Defaults to `gemini/gemini-1.5-flash`. |

## Original vs Improved: Key Differences

| Aspect | Original (252 lines) | Improved (633 lines) |
| ------ | -------------------- | -------------------- |
| **Batch tool** | `read_all_files()` | `read_all_files()` with `pathlib.Path`, 10 MB size limit, per-file error isolation |
| **Search** | ❌ None | ✅ `search_files` tool |
| **Output formatting** | Basic print | `format_result_summary()` for cleaner result display |
| **CLI** | `--mock`, `--task` | Full: `--task`, `--model`, `--max-iterations`, `--verbose` |
| **Structure** | Inline script | Structured `run_agent()`, `execute_tool()`, `validate_api_key()`, `main()` |
| **Default model** | `openai/gpt-4` | `gemini/gemini-1.5-flash` |
| **Helper** | `summarize_file_content()` (heuristic) | `format_result_summary()` (result display) |

## 🎯 What Makes This "Enhanced"?

This agent builds on the simple function calling agent by adding:

✅ **Batch Operations**: Read all files at once instead of one-by-one  
✅ **Better Efficiency**: Fewer iterations for multi-file tasks  
✅ **Enhanced Tools**: More sophisticated file operations  
✅ **CLI Integration**: Run with command-line arguments  
✅ **Better Summaries**: Cleaner result displays

## 🔥 Key Feature: Batch File Reading

### The Problem with Sequential Reading

**Simple Agent (Inefficient):**

```bash
Task: "Summarize all Python files"

Iteration 1: list_files() → ["a.py", "b.py", "c.py"]
Iteration 2: read_file("a.py") → "contents..."
Iteration 3: read_file("b.py") → "contents..."
Iteration 4: read_file("c.py") → "contents..."
Iteration 5: terminate(summary)

Total: 5 iterations, 4 API calls
```

**Enhanced Agent (Efficient):**

```bash
Task: "Summarize all Python files"

Iteration 1: read_all_files(".") → {"a.py": "...", "b.py": "...", "c.py": "..."}
Iteration 2: terminate(summary)

Total: 2 iterations, 1 API call
💰 60% cost reduction!
```

## 🌟 Features

- **Batch File Reading**: Read multiple files in one operation
- **Flexible Path Support**: Work with different directories
- **Smart Result Formatting**: Concise summaries in output (`format_result_summary()` in improved version)
- **CLI Task Specification**: Run without interaction
- **Error Recovery**: Handles individual file errors gracefully (improved version)
- **Size Validation**: Prevents reading huge files (10 MB limit in improved version)

## 🛠️ Available Tools

| Tool | Description | When to Use | Available In |
| ------ | ------------- | ------------- | ------------- |
| `list_files(path)` | List files in directory | See what's available | Both |
| `read_file(file_name)` | Read single file | Need one specific file | Both |
| `read_all_files(directory)` | Read ALL files at once | Need multiple files | Both |
| `search_files(pattern)` | Find files by pattern | Find specific file types | **Improved only** |
| `terminate(message)` | End with summary | Task complete | Both |

*Note: The improved version adds `search_files` and enhances `read_all_files` with size checking and error isolation.*

## 🚀 Quick Start

### Installation

```bash
pip install litellm python-dotenv
echo "GEMINI_API_KEY=your-key" > .env
```

### Basic Usage

```bash
# Interactive (original)
python agent_loop_with_function_calling2.py

# Direct task
python agent_loop_with_function_calling2.py --task "Read all Python files"

# Improved version - full CLI
python agent_loop_with_function_calling2_improved.py --task "Read all Python files"

# Verbose mode (improved)
python agent_loop_with_function_calling2_improved.py --verbose

# Custom model
python agent_loop_with_function_calling2_improved.py --model openai/gpt-4
```

## 📝 Example Sessions

### Example 1: Efficient Multi-File Reading

```bash
Task: "Read all Python files and create a summary"

Iteration 1:
  Tool: read_all_files
  Args: directory="."
  Result: 3 files read
  Files: {
    "main.py": "...",
    "agent.py": "...",
    "utils.py": "..."
  }

Iteration 2:
  Tool: terminate
  Args: message="Project contains 3 Python files:
        - main.py: Entry point
        - agent.py: Agent implementation
        - utils.py: Helper functions"
  ✅ COMPLETED

Total: 2 iterations (vs 5 with sequential reading!)
```

### Example 2: Directory Analysis

```bash
Task: "Analyze all files in the 'docs' directory"

Iteration 1:
  Tool: read_all_files
  Args: directory="docs"
  Result: 5 files read

Iteration 2:
  Tool: terminate
  Args: message="Documentation contains:
        - README.md: Project overview
        - API.md: API documentation
        - GUIDE.md: User guide
        - FAQ.md: Common questions
        - CHANGELOG.md: Version history"
  ✅ COMPLETED
```

## 🔧 When to Use Each Tool

### read_file() - Single File

```python
# Use when:
✅ Need only one specific file
✅ File name is known
✅ Quick lookup

# Example task:
"Read the README.md file"
```

### read_all_files() - Batch Operation

```python
# Use when:
✅ Need multiple/all files
✅ Don't know exact filenames
✅ Want efficiency
✅ Processing entire directory

# Example tasks:
"Read all Python files"
"Analyze all markdown files"
"Summarize all logs"
```

### search_files() - Pattern Matching (Improved version)

```python
# Use when:
✅ Need files matching pattern
✅ Filtering by extension
✅ Finding specific file types

# Example tasks:
"Find all test files"
"List all .json files"
"Get files starting with 'config'"
```

## 📊 Efficiency Comparison

| Task Type | Simple Agent | Enhanced Agent | Savings |
| ----------- | -------------- | ---------------- | --------- |
| Read 1 file | 2 iterations | 2 iterations | 0% |
| Read 5 files | 6 iterations | 2 iterations | 67% |
| Read 10 files | 11 iterations | 2 iterations | 82% |
| Read 20 files | 21 iterations | 2 iterations | 90% |

**Cost Impact:**

- Simple: 21 API calls × $0.02 = $0.42
- Enhanced: 2 API calls × $0.02 = $0.04
- **Savings: 90%** 💰

## 🎓 Understanding Batch Operations

### How read_all_files() Works

```python
def read_all_files(directory: str = ".") -> Dict[str, str]:
    result = {}
    
    for file in directory:
        try:
            result[file.name] = file.read_text()
        except Exception as e:
            result[file.name] = f"Error: {e}"
    
    return result
```

**Returns:**

```python
{
    "file1.txt": "contents of file 1...",
    "file2.txt": "contents of file 2...",
    "file3.txt": "Error: Not a text file"
}
```

### Error Handling in Batch Operations

Individual file errors don't stop the whole operation (improved version):

```python
{
    "readable.txt": "file contents",
    "binary.dat": "Error: Not a text file",
    "huge.log": "Error: File too large (15.5MB)"
}
```

The agent sees what succeeded and what failed, then adapts.

### format_result_summary() — Notable Improvement

The improved version includes `format_result_summary()` to present tool results in a cleaner, more readable format. Instead of dumping raw JSON or long strings, it produces concise summaries that make it easier for users (and the agent) to understand batch read results, file counts, and error conditions.

## 🎯 Use Cases

### Perfect For

✅ **Code Analysis**

```bash
"Read all Python files and identify the main entry point"
"Find all test files and list what they test"
```

✅ **Documentation Review**

```bash
"Read all markdown files and create a table of contents"
"Summarize all documentation in the docs/ folder"
```

✅ **Log Analysis**

```bash
"Read all log files and find errors"
"Analyze all logs from today"
```

✅ **Configuration Management**

```bash
"Read all config files and verify settings"
"Compare configuration across environments"
```

### Not Ideal For

❌ **Single file operations** → Use simple agent  
❌ **Very large directories** → Files may exceed limits  
❌ **Binary files** → Only text files supported  

## 🔍 Comparison with Simple Agent

| Aspect | Simple Agent | Enhanced Agent |
| -------- | -------------- | ---------------- |
| **Batch Operations** | ❌ No | ✅ Yes |
| **API Calls (10 files)** | 11 | 2 |
| **Cost Efficiency** | Baseline | 80%+ savings |
| **Complexity** | Low | Low-Medium |
| **Best For** | 1-2 files | Multiple files |
| **Code Size** | 200 lines | 250–630 lines |

## ⚙️ Configuration

### Environment Variables

```env
DEFAULT_MODEL=gemini/gemini-1.5-flash
DEFAULT_MAX_ITERATIONS=10
GEMINI_API_KEY=your-key
```

### Command-Line Options

```bash
--task "Task description"   # Run non-interactively
--model MODEL_NAME          # Specify model (improved)
--max-iterations N          # Set iteration limit (improved)
--verbose                   # Detailed output (improved)
--mock                      # Mock mode without LLM (original only)
```

## 🔧 Adding Custom Batch Operations

### Example: Batch File Statistics

```python
def analyze_all_files(directory: str = ".") -> Dict[str, Dict]:
    """Get statistics for all files."""
    stats = {}
    
    for file in Path(directory).iterdir():
        if file.is_file():
            stats[file.name] = {
                "size": file.stat().st_size,
                "lines": len(file.read_text().splitlines()),
                "extension": file.suffix
            }
    
    return stats

# Add to registry
TOOL_FUNCTIONS["analyze_all_files"] = analyze_all_files

# Add to tools
TOOLS.append({
    "type": "function",
    "function": {
        "name": "analyze_all_files",
        "description": "Get statistics for all files in directory",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string"}
            }
        }
    }
})
```

## 🐛 Troubleshooting

### "File too large" Errors

**Problem**: Some files exceed 10MB limit (improved version)

**Solutions**:

1. Filter files before reading: `search_files("*.py")`
2. Increase size limit (edit MAX_SIZE)
3. Read files sequentially instead

### "Not a text file" Errors

**Problem**: Binary files can't be read as text

**Solution**: Files with errors are reported but don't stop batch operation

```python
{
    "data.txt": "contents...",
    "image.png": "Error: Not a text file",  # Graceful degradation
    "document.pdf": "Error: Not a text file"
}
```

### Too Many Files

**Problem**: Directory has 100+ files

**Solutions**:

1. Use `search_files()` to filter first (improved version)
2. Process subdirectories separately
3. Increase iteration limit

## 💰 Cost Optimization

### Strategies

1. **Use batch operations** when possible

   ```bash
   # Good: 2 iterations
   --task "Read all Python files"
   
   # Avoid: 10+ iterations
   --task "Read main.py, then agent.py, then utils.py..."
   ```

2. **Filter before reading** (improved version)

   ```bash
   # Filter first, then read
   search_files("*.py") → read_all_files()
   ```

3. **Use efficient models**

   ```bash
   --model gemini/gemini-1.5-flash  # Free tier
   ```

### Cost Example

**Task**: Analyze 20 Python files

| Approach | Iterations | Cost (GPT-4) |
| ---------- | ------------ | -------------- |
| Sequential | 22 | $0.44 |
| Batch | 2 | $0.04 |
| **Savings** | **91%** | **$0.40** |

## 🎓 Best Practices

### 1. Choose Right Tool for Task

```python
# Single file → read_file
"Read config.json"

# Multiple files → read_all_files
"Read all config files"

# Filter needed → search_files + read_all_files (improved)
"Find and read all test files"
```

### 2. Handle Errors Gracefully

Agent sees errors but continues:

```python
result = {
    "good.txt": "contents",
    "bad.txt": "Error: ...",  # Agent can adapt
}
```

### 3. Provide Clear Tasks

```bash
# Clear ✅
--task "Read all Python files and list their main functions"

# Vague ❌
--task "Do something with files"
```

## 🚀 Advanced Patterns

### Pattern 1: Filtered Batch Reading (Improved version)

```python
Task: "Read all test files"

Step 1: search_files("test_*.py")
Step 2: read_all_files()  # Only reads test files
```

### Pattern 2: Directory-Specific Analysis

```python
Task: "Compare src and test directories"

Step 1: read_all_files("src")
Step 2: read_all_files("test")
Step 3: terminate(comparison)
```

### Pattern 3: Progressive Reading

```python
Task: "Find and analyze error logs"

Step 1: search_files("*.log")
Step 2: read_all_files() if < 10 files, else read_file() selectively
```

## 📊 Performance Tips

1. **Batch when possible**: Use `read_all_files` for multiple files
2. **Filter first**: Use `search_files` before reading (improved version)
3. **Limit scope**: Read specific directories, not entire filesystem
4. **Check sizes**: Tool automatically skips files > 10MB (improved version)

## 🔒 Security Considerations

### Path Validation

```python
# Prevent directory traversal
if ".." in path or path.startswith("/"):
    return "Error: Invalid path"
```

### Size Limits

```python
# Prevent memory issues
MAX_SIZE = 10 * 1024 * 1024  # 10MB per file
```

### Error Isolation

```python
# One bad file doesn't crash everything
try:
    content = read_file(f)
except Exception as e:
    content = f"Error: {e}"  # Continue with others
```

## 📚 Further Reading

- [Batch Processing Patterns](https://en.wikipedia.org/wiki/Batch_processing)
- [File I/O Best Practices](https://docs.python.org/3/tutorial/inputoutput.html)
- [LLM Function Calling](https://docs.litellm.ai/)

## 🤝 When to Use This vs Others

**Use Enhanced Agent When:**

- Need to read multiple files efficiently
- Processing directories of files
- Want to minimize API calls
- Working with file collections

**Use Simple Agent When:**

- Only need one or two files
- Don't need batch operations
- Want minimal code
- Learning function calling basics

**Use Framework When:**

- Building complex systems
- Need modular architecture
- Production deployment
- Multiple goal types
