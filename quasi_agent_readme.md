# Comparison Guide: Simple LLM Test vs Quasi-Agent

A beginner's guide to understanding the differences between these scripts.

## Files Covered

This readme covers two quasi-agent implementations:

| File | Lines | Description |
|------|-------|-------------|
| **quasi-agent.py** | 247 | Original implementation with caching, 3-step workflow, and basic CLI |
| **quasi_agent_improved.py** | 579 | Enhanced version with better prompts, dual API key support, `--no-cache`, and comprehensive documentation |

---

## Original vs Improved Quasi-Agent

| Feature | quasi-agent.py (Original) | quasi_agent_improved.py (Improved) |
|---------|---------------------------|-------------------------------------|
| **API Keys** | GEMINI_API_KEY only | Both GEMINI_API_KEY and OPENAI_API_KEY via `validate_api_key()` |
| **Caching** | SHA-256 keys, `.llm_cache/` dir | Same, plus `--no-cache` flag to disable |
| **Cache Control** | Always on (unless env overrides) | `cache_enabled` parameter, `--no-cache` CLI flag |
| **Module Docstring** | ❌ No | ✅ Yes (purpose, workflow overview) |
| **Prompts** | Simple instructions | Numbered requirements (e.g., "1. Use clear names...") |
| **Output File** | Function + tests only | Auto-generated docstring header + function + tests |
| **Output Stats** | ❌ No | ✅ Line count, file size |
| **Formatting** | Plain text | Emoji indicators (✅, 🔄, 💾, ⚠️, etc.) |
| **Function Docstrings** | Minimal | Comprehensive (Args, Returns, Raises) |
| **Default Model** | openai/gpt-4 | gemini/gemini-1.5-flash |
| **CLI Args** | `--model`, `--mock`, `--verbose` | Same + `--no-cache` |
| **Error Handling** | Basic | KeyboardInterrupt, verbose traceback option |

### CLI Usage Examples

**Original (quasi-agent.py):**

```bash
python quasi-agent.py
python quasi-agent.py --model openai/gpt-4
python quasi-agent.py --mock --verbose
```

**Improved (quasi_agent_improved.py):**

```bash
python quasi_agent_improved.py
python quasi_agent_improved.py --model gemini/gemini-1.5-flash
python quasi_agent_improved.py --mock --verbose
python quasi_agent_improved.py --no-cache          # Disable caching (fresh API calls every time)
python quasi_agent_improved.py --no-cache --verbose
```

---

## 📊 Quick Comparison: main.py vs Quasi-Agent

| Feature | main.py (Simple) | quasi-agent.py (Advanced) |
| --------- | ------------------- | --------------------------- |
| **Purpose** | Test API connection | Generate complete functions |
| **Steps** | Single API call | Multi-step workflow (3+ calls) |
| **Memory** | No conversation history | Maintains context between steps |
| **Output** | Prints response | Creates Python files |
| **Caching** | ❌ No | ✅ Yes (saves money!) |
| **Complexity** | Beginner-friendly | Intermediate |
| **Use Case** | Testing, learning | Actual code generation |

## 🎯 When to Use Each

### Use `main.py` When You Want To

- ✅ Test if your API key works
- ✅ Learn how LLM APIs work
- ✅ Make simple, one-off requests
- ✅ Debug API connection issues
- ✅ Understand basic retry logic

### Use `quasi-agent.py` When You Want To

- ✅ Generate actual code you'll use
- ✅ Learn about AI agents
- ✅ Automate repetitive coding tasks
- ✅ Understand multi-step AI workflows
- ✅ See caching in action

### Use `quasi_agent_improved.py` When You Want To

- ✅ Everything above, plus:
- ✅ Support for both Gemini and OpenAI keys
- ✅ Option to disable caching with `--no-cache` (e.g., for fresh results)
- ✅ Better prompts and output formatting
- ✅ More detailed documentation and error handling

## 🔍 Side-by-Side Code Comparison

### 1. Simple Request (main.py)

```python
# Single API call
messages = [{"role": "user", "content": "Say hello"}]
response = call_with_retries(api_key, model, messages)
print(response)
```

**Output:**

```bash
Hello! How can I help you today?
```

### 2. Multi-Step Agent (quasi-agent.py / quasi_agent_improved.py)

```python
# Step 1: Generate
messages = [
    {"role": "system", "content": "You are an expert..."},
    {"role": "user", "content": "Write a function..."}
]
code = generate_response(messages)

# Step 2: Document (builds on Step 1)
messages.append({"role": "assistant", "content": code})
messages.append({"role": "user", "content": "Add documentation..."})
documented = generate_response(messages)

# Step 3: Test (builds on Steps 1 & 2)
messages.append({"role": "assistant", "content": documented})
messages.append({"role": "user", "content": "Add tests..."})
tests = generate_response(messages)

# Save final result
save_to_file(documented + tests)
```

**Output:**

```bash
calculates_factorial.py (with function, docs, and tests)
```

## 🧩 Key Concepts Explained

### 1. Conversation History

**Simple Version (No Memory):**

```python
# Each call is independent
call_1 = ask("What's 2+2?")  # → "4"
call_2 = ask("What about that plus 3?")  # → "?" (doesn't remember)
```

**Agent Version (With Memory):**

```python
messages = []
messages.append({"role": "user", "content": "What's 2+2?"})
response_1 = ask(messages)  # → "4"

messages.append({"role": "assistant", "content": response_1})
messages.append({"role": "user", "content": "What about that plus 3?"})
response_2 = ask(messages)  # → "7" (remembers previous answer!)
```

### 2. Caching

**Without Caching (main.py):**

```python
# Every request costs money
ask("Hello") → API call → $
ask("Hello") → API call → $  # Same request, pay again!
ask("Hello") → API call → $  # Still paying!
```

**With Caching (quasi-agent.py / quasi_agent_improved.py):**

```python
# First request: cache miss, make API call
ask("Hello") → API call → $ → save to cache

# Subsequent requests: cache hit, free!
ask("Hello") → read cache → FREE ✅
ask("Hello") → read cache → FREE ✅
```

**Disabling Cache (quasi_agent_improved.py only):**

```bash
python quasi_agent_improved.py --no-cache
# Every request hits the API (useful when you want fresh results)
```

### 3. Error Handling

Both scripts handle errors, but differently:

**Simple Version:**

```python
try:
    response = api_call()
except RateLimitError:
    wait_and_retry()
except Exception as e:
    print(f"Error: {e}")
    raise
```

**Agent Version (More Detailed):**

```python
try:
    response = api_call()
except RateLimitError:
    print("⚠️ Rate limited, retrying...")
    wait_and_retry()
except Exception as e:
    print(f"❌ Error in step {current_step}")
    if verbose:
        show_full_traceback()
    raise
```

## 📈 Progression Path

Learn in this order:

```bash
1. main.py (Simple Test)
   └─ Learn: API basics, retry logic
   
2. Modify main.py
   └─ Learn: Customization, different prompts
   
3. quasi-agent.py (Original Agent)
   └─ Learn: Multi-step workflows, caching
   
4. quasi_agent_improved.py (Enhanced Agent)
   └─ Learn: Better prompts, --no-cache, dual API keys
   
5. Build Your Own Agent
   └─ Learn: Custom workflows, tool use
```

## 🎓 What Each Script Teaches

### main.py Teaches You

1. **Basic API Calls**

   ```python
   response = completion(model="gpt-4", messages=[...])
   ```

2. **Retry Logic**

   ```python
   for attempt in range(max_retries):
       try:
           return api_call()
       except RateLimitError:
           time.sleep(exponential_backoff(attempt))
   ```

3. **Environment Variables**

   ```python
   api_key = os.getenv("OPENAI_API_KEY")
   ```

4. **Command-Line Arguments**

   ```python
   parser.add_argument('--mock', action='store_true')
   ```

### quasi-agent.py Teaches You

1. **Conversation Management**

   ```python
   messages = []
   for step in workflow:
       messages.append(user_message)
       response = api_call(messages)
       messages.append(assistant_message)
   ```

2. **Caching Strategy**

   ```python
   cache_key = hash(request)
   if cache_key in cache:
       return cache[cache_key]
   ```

3. **Multi-Step Workflows**

   ```python
   step1_output = generate()
   step2_output = document(step1_output)
   step3_output = test(step2_output)
   ```

4. **String Processing**

   ```python
   code = extract_code_block(markdown_response)
   ```

## 💡 Practical Examples

### Example 1: Just Testing Your Setup

**Use main.py:**

```bash
python main.py --mock
python main.py  # Real API call
```

Good for: Making sure everything is installed correctly.

### Example 2: Need Actual Code

**Use quasi-agent.py or quasi_agent_improved.py:**

```bash
python quasi-agent.py
> "validates email addresses"

# Or with the improved version (supports both Gemini and OpenAI):
python quasi_agent_improved.py
> "validates email addresses"
```

Good for: Getting production-ready code.

### Example 3: Learning API Behavior

**Use main.py with modifications:**

```python
# Try different prompts
messages = [{"role": "user", "content": "Explain quantum computing"}]
```

Good for: Understanding how the AI responds.

### Example 4: Automating Repetitive Tasks

**Use quasi-agent.py or quasi_agent_improved.py:**

```bash
# Generate multiple utility functions
python quasi-agent.py  # "calculates factorial"
python quasi-agent.py  # "checks palindrome"
python quasi-agent.py  # "sorts dictionary"

# With improved version, use --no-cache when you want fresh results each time:
python quasi_agent_improved.py --no-cache  # "calculates factorial"
```

Good for: Building a personal function library.

## 🔧 Customization Examples

### Customizing main.py

```python
# Add conversation
messages = [
    {"role": "user", "content": "Write a haiku about Python"},
]

# Use different parameters
response = call_with_retries(
    api_key,
    model="gpt-4",
    messages=messages,
    temperature=0.7,  # More creative
)
```

### Customizing quasi-agent.py

```python
# Change the workflow
def develop_custom_class():
    # Step 1: Generate class
    # Step 2: Add methods
    # Step 3: Add properties
    # Step 4: Add tests
    pass

# Add validation step
def develop_with_validation():
    code = generate_code()
    tests = generate_tests()
    results = run_tests(tests)
    if not results.passed:
        code = fix_code(code, results)
    return code
```

## 🎯 Which Should You Start With?

### Complete Beginner?

### Start with main.py

- Simpler to understand
- Fewer moving parts
- See immediate results
- Learn API basics

### Some Python Experience?

**Try both in order:**

1. Run `main.py` to understand basics
2. Move to `quasi-agent.py` to see real applications
3. Try `quasi_agent_improved.py` for enhanced features

### Want to Build Something?

### Jump to quasi-agent.py (or quasi_agent_improved.py)

- Actually generates useful code
- Learn by example
- Modify the workflow for your needs

## 📚 Learning Resources

### After main.py

- Try modifying the test message
- Experiment with different models
- Add more command-line options
- Implement custom retry strategies

### After quasi-agent.py

- Add a new step to the workflow
- Implement different code styles
- Create other types of agents
- Build a chatbot or tool

## 🤔 Common Questions

### Q: Can I use main.py for real projects?

**A:** It's designed for testing, but you can build on it. For real projects, use something like quasi-agent.py with proper error handling and file management.

### Q: Is quasi-agent.py too complex for beginners?

**A:** Start with main.py first, then move to quasi-agent.py. The concepts build on each other.

### Q: Which one costs more to run?

**A:** Quasi-agent.py makes 3+ API calls but has caching, so repeated requests are free. Main.py makes 1 call but no caching. Use `--no-cache` in quasi_agent_improved.py when you want fresh results (each run will hit the API).

### Q: Can I combine them?

**A:** Absolutely! Use the caching from quasi-agent.py in main.py, or use the simple retry logic from main.py in your own projects.

### Q: What's the difference between quasi-agent.py and quasi_agent_improved.py?

**A:** The improved version adds a module docstring, dual API key support (Gemini + OpenAI), the `--no-cache` flag, enhanced prompts with numbered requirements, file headers with auto-generated docstrings, output statistics, emoji formatting, and comprehensive docstrings. See the "Original vs Improved Quasi-Agent" table above.

## 🎉 Summary

| Aspect | main.py | quasi-agent.py | quasi_agent_improved.py |
| --------- | --------------- | --------------------------- | --------------------------- |
| **Goal** | Learn API basics | Generate real code | Generate real code (enhanced) |
| **Steps** | 1 (single call) | 4 (multi-step) | 4 (multi-step) |
| **Cost** | Low (1 call) | Medium (3-4 calls, but cached) | Medium (3-4 calls, cached unless `--no-cache`) |
| **Output** | Terminal text | Python file | Python file (with header, stats) |
| **Learning Curve** | Gentle | Moderate | Moderate |
| **Production Ready** | ❌ | ✅ | ✅ |
| **Cache Control** | N/A | Always on | `--no-cache` flag |
