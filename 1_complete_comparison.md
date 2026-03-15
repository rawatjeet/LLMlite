# Complete Comparison: Simple Test → Quasi-Agent → Tool Agent

A comprehensive guide comparing all three core scripts to understand the progression from simple API calls to autonomous agents. Each script has an **original** version (concise, learning-focused) and an **improved** version (production-ready, well-documented).

## The Three Levels

```
Level 1: main.py / main_improved.py (Simple Test)
    ↓ Add multi-step workflow
Level 2: quasi-agent.py / quasi_agent_improved.py (Fixed Workflow)
    ↓ Add autonomous decision-making
Level 3: agent_tools.py / agent_tools_improved.py (True Agent)
```

## File Inventory

| Level | Original File | Improved File | Purpose |
|-------|--------------|---------------|---------|
| 1 | `main.py` | `main_improved.py` | Test API connection with retry logic |
| 2 | `quasi-agent.py` | `quasi_agent_improved.py` | Multi-step function generation |
| 3 | `agent_tools.py` | `agent_tools_improved.py` | Autonomous agent with JSON action parsing |

## Feature Matrix

| Feature | main.py | quasi-agent.py | agent_tools.py |
|---------|---------|----------------|----------------|
| **Complexity** | Beginner | Intermediate | Advanced |
| **API Calls** | 1 | 3+ (fixed) | Variable (adaptive) |
| **Decision Making** | None | None | Autonomous |
| **Conversation Memory** | No | Yes | Yes |
| **Tool Execution** | No | No | Yes (list, read, write, search) |
| **Caching** | No | Yes | No* |
| **Loops/Iteration** | No | No | Yes |
| **Adapts Strategy** | No | No | Yes |
| **Output** | Terminal text | Python file | Task completion |
| **Use Case** | Testing API | Code generation | Task automation |
| **CLI Arguments** | `--mock`, `--retries` | `--model`, `--mock`, `--no-cache` | `--task`, `--verbose`, `--max-iterations` |

*Could be added

## Original vs Improved Versions

### What the Improved Versions Add

| Improvement | main_improved | quasi_agent_improved | agent_tools_improved |
|-------------|---------------|---------------------|---------------------|
| Module docstring | Yes | Yes | Yes |
| Comprehensive docstrings | Yes | Yes | Yes |
| Type hints throughout | Partial | Yes | Yes |
| API key validation function | Yes | Yes | Yes |
| `main()` entry point | Yes | Yes | Yes |
| argparse with epilog/examples | Yes | Yes | Yes |
| Formatted output with emojis | Yes | Yes | Yes |
| Graceful error handling | Yes | Yes | Yes |
| `--verbose` flag | No | Yes | Yes |
| `--no-cache` flag | N/A | Yes | N/A |
| System prompt for agent | N/A | Enhanced | Dynamic generation |
| Additional tools | N/A | N/A | `write_file`, `search_files` |
| `pathlib.Path` usage | No | No | Yes |
| File size validation | N/A | N/A | Yes (10 MB limit) |

### Key Code Differences

**main.py (Original)** — 67 lines, inline `call_with_retries()`, hardcoded model `gpt-4.1`.

**main_improved.py** — 220 lines, `load_api_key()` function, `run_test_call()` wrapper, structured `main()`, model configurable via `--model`.

**quasi-agent.py (Original)** — 247 lines, has caching, SHA-256 cache keys, `extract_code_block()`, direct `input()` for user interaction.

**quasi_agent_improved.py** — 579 lines, adds `validate_api_key()`, `--no-cache` CLI flag, better prompts with numbered requirements, file header with docstring, output statistics (line count, file size).

**agent_tools.py (Original)** — 172 lines, custom JSON action parsing from `\`\`\`action` blocks, `list_files` + `read_file` + `terminate` tools, flat script structure.

**agent_tools_improved.py** — 678 lines, adds `write_file` + `search_files` tools, `safe_json_parse()`, `get_system_prompt()` with dynamic tool schema injection, proper `run_agent()` function, `execute_tool()` with error handling, structured CLI.

## Visual Comparison

### 1. Execution Flow

**main.py (Linear):**

```
User Input → Single API Call → Print Response → Done
```

**quasi-agent.py (Sequential):**

```
User Input → Generate Function → Add Docs → Add Tests → Save File
    ↓            ↓                ↓            ↓         ↓
  Fixed        Fixed            Fixed        Fixed    Done
```

**agent_tools.py (Adaptive Loop):**

```
                    ┌──────────────────┐
                    ↓                  │
User Task → Think → Choose Tool → Execute → Success?
                         │                     ↓ No
                         └─────────────────────┘
                                              │ Yes
                                              ↓
                                           Done
```

### 2. Code Comparison

**Simple Request (main.py):**

```python
messages = [{"role": "user", "content": "Say hello"}]
response = call_with_retries(api_key, model, messages)
print(response)
```

**Fixed Workflow (quasi-agent.py):**

```python
messages = []

# Step 1: Always generate function
messages.append({"role": "user", "content": "Write function..."})
code = generate_response(messages)

# Step 2: Always add docs
messages.append({"role": "assistant", "content": code})
messages.append({"role": "user", "content": "Add docs..."})
documented = generate_response(messages)

# Step 3: Always add tests
messages.append({"role": "assistant", "content": documented})
messages.append({"role": "user", "content": "Add tests..."})
tests = generate_response(messages)
```

**Autonomous Loop (agent_tools.py):**

```python
messages = [{"role": "user", "content": user_task}]

while not done:
    response = generate_response(messages)
    action = parse_action(response)   # AI chooses action

    if action["tool_name"] == "list_files":
        result = list_files()
    elif action["tool_name"] == "read_file":
        result = read_file(action["args"]["file_name"])
    elif action["tool_name"] == "terminate":
        done = True

    messages.append({"role": "user", "content": json.dumps(result)})
```

## Capability Progression

### Level 1: main.py

**Can do:**

- Send single prompts
- Test API connection
- Handle rate limits with exponential backoff
- Parse responses
- Mock mode for testing without API credits

**Cannot do:**

- Multi-step tasks
- Remember context between calls
- Execute actions on the system
- Make decisions

**Example tasks:** "Say hello", "Explain quantum computing", "Write a haiku"

### Level 2: quasi-agent.py

**Can do:**

- Everything from Level 1
- Multi-step workflows (generate → document → test → save)
- Maintain conversation context across steps
- Build on previous outputs
- Cache responses to save money
- Extract code from markdown blocks

**Cannot do:**

- Choose different execution paths
- Execute external tools
- Adapt to intermediate results
- Handle unexpected situations

**Example tasks:** "Create a function that calculates factorial", "Generate a class for user management"

### Level 3: agent_tools.py

**Can do:**

- Everything from Level 2
- Make autonomous decisions about which tool to use
- Execute Python tools (list_files, read_file, write_file, search_files)
- Adapt strategy based on intermediate results
- Handle errors dynamically and try alternatives
- Variable-length workflows (1 to N iterations)

**Cannot do:**

- Learn from experience (no persistent memory)
- Create new tools at runtime
- Access external systems without predefined tools

**Example tasks:** "Find all Python files and summarize them", "Read the README and create a project overview", "Search for test files and analyze their structure"

## When to Use Each

### Use main.py When

- Testing your setup or API key
- Learning how LLM APIs work
- Making simple, one-off requests
- Debugging API connection issues

```bash
python main.py --mock       # Test without API credits
python main.py              # Real API call
```

### Use quasi-agent.py When

- Generating complete Python code with docs and tests
- Following a fixed multi-step workflow
- Building on previous outputs sequentially
- Want caching to avoid duplicate API costs

```bash
python quasi-agent.py
> "validates email addresses"
# → Gets function + docs + tests in one file
```

### Use agent_tools.py When

- Tasks need tool use (file system operations)
- Unknown number of steps required
- Need adaptive approach to problem-solving
- Real-world automation scenarios

```bash
python agent_tools.py --task "Find and summarize all Python files"
```

## Real-World Examples

### Example 1: "Say Hello"

| Script | Suitability | Steps | Output |
|--------|-------------|-------|--------|
| main.py | Perfect | 1 | "Hello! How can I help you?" |
| quasi-agent.py | Not suitable | N/A | Designed for code generation |
| agent_tools.py | Overkill | 1 (terminate) | Terminates immediately |

### Example 2: "Create a factorial function"

| Script | Suitability | Steps | Output |
|--------|-------------|-------|--------|
| main.py | Incomplete | 1 | Raw code, no docs or tests |
| quasi-agent.py | Perfect | 3 | Complete file with function, docs, tests |
| agent_tools.py | Wrong tool | Multiple | No code generation tools |

### Example 3: "Analyze Python files in directory"

| Script | Suitability | Steps | Output |
|--------|-------------|-------|--------|
| main.py | Cannot do | N/A | No file access |
| quasi-agent.py | Creates code only | 3 | Generates analyzer code, doesn't run it |
| agent_tools.py | Perfect | 3-5 | Reads actual files and provides analysis |

## Technical Deep Dive

### Memory Management

**main.py** — No memory. Each call is independent.

**quasi-agent.py** — Sequential memory. Appends user/assistant messages to build context across 3 steps.

**agent_tools.py** — Full conversation memory. Accumulates tool calls and results over N iterations, enabling the agent to reference all prior actions.

### Error Handling

**main.py** — Retry with exponential backoff for `RateLimitError`.

**quasi-agent.py** — Retry + caching. Cached responses bypass the API entirely.

**agent_tools.py** — Dynamic error recovery. If a tool fails, the error is fed back to the agent, which can try a different approach.

### Caching (quasi-agent.py only)

```python
cache_key = SHA256(messages + options)

if cache_key in cache_dir:
    return cached_value         # Free, instant

response = call_llm(messages)
write_cache(cache_dir, cache_key, response)
return response
```

Cache files are stored in `.llm_cache/` by default (configurable via `LLM_CACHE_DIR` env var).

## Cost Comparison

### Per Task (Average)

| Metric | main.py | quasi-agent.py | agent_tools.py |
|--------|---------|----------------|----------------|
| API Calls | 1 | 3 | 3-10 (variable) |
| Cost (Gemini) | Free | Free | Free (up to limits) |
| Cost (GPT-4) | ~$0.02 | ~$0.06 | ~$0.06-0.20 |
| Time | <1 second | 3-5 seconds | 5-15 seconds |
| Caching benefit | None | Repeats are free | None |

## Learning Path

### Week 1: Foundations

```
Day 1-2: Set up environment, run main.py and main_improved.py
Day 3-4: Understand API calls, modify prompts
Day 5-7: Experiment with different models and parameters
```

### Week 2: Multi-Step AI

```
Day 1-2: Run quasi-agent.py, understand the 3-step workflow
Day 3-4: Compare original vs improved version
Day 5-7: Add a custom 4th step (e.g., performance optimization)
```

### Week 3: Autonomous Agents

```
Day 1-2: Run agent_tools.py, understand tool calling
Day 3-4: Compare original (JSON parsing) vs improved (more tools)
Day 5-7: Add a custom tool and build your own agent
```

## Decision Flowchart

```
Start: I have a task
    ↓
Is it a single simple question?
    ↓ Yes → Use main.py
    ↓ No
Do I need to generate code with docs and tests?
    ↓ Yes → Use quasi-agent.py
    ↓ No
Does it require file/system operations?
    ↓ Yes → Use agent_tools.py
    ↓ No
Will the number of steps vary based on results?
    ↓ Yes → Use agent_tools.py
    ↓ No → Use quasi-agent.py or main.py
```

## Next Steps After Mastery

1. **Combine approaches** — Use caching from quasi-agent in the tool agent; add tool calling to quasi-agent
2. **Build specialized agents** — Code review agent, documentation agent, testing agent
3. **Advanced patterns** — Multi-agent systems, memory persistence, learning capability
4. **Production deployment** — Error recovery, monitoring, rate limiting, cost control

## Summary Table

| Aspect | main.py | quasi-agent.py | agent_tools.py |
|--------|---------|----------------|----------------|
| **Best For** | Testing, learning | Code generation | Task automation |
| **Complexity** | Simple | Medium | Complex |
| **Flexibility** | Low | Medium | High |
| **Power** | Low | Medium | High |
| **Cost/Task** | Lowest | Medium | Varies |
| **Learning Curve** | Gentle | Moderate | Steep |
| **Production Ready** | No | Yes (for code gen) | Yes (for automation) |
| **Original Lines** | 67 | 247 | 172 |
| **Improved Lines** | 220 | 579 | 678 |

---

## Key Takeaways

1. **main.py** — Foundation: learn API basics, retry logic, environment variables
2. **quasi-agent.py** — Multi-step: fixed workflows, conversation memory, caching
3. **agent_tools.py** — Autonomous: adaptive behavior, tool execution, agent loops
