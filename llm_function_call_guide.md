# LLM Function Calling - Beginner's Guide

## What Does This Code Do?

This Python script creates an AI agent that can interact with files on your computer. When you ask it questions about files, it automatically uses the right tools to answer you.

**Example:**

- You ask: "What files are in this folder?"
- The AI calls the `list_files()` function
- You get a list of all files!

## How It Works (Step by Step)

### 1. **Setting Up**

```python
from dotenv import load_dotenv
load_dotenv()
```

This loads your secret API key from a `.env` file (keeps your key safe and separate from your code).

### 2. **Defining Tools**

The script creates two "tools" (functions) the AI can use:

- **`list_files()`** - Shows all files in the current folder
- **`read_file(file_name)`** - Reads the content of a specific file

Think of these as tools in a toolbox. The AI decides which tool to use based on what you ask.

### 3. **Tool Descriptions**

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Returns a list of files in the directory.",
            ...
        }
    }
]
```

These descriptions tell the AI what each tool does, so it knows when to use them.

### 4. **The Conversation**

```python
user_task = input("What would you like me to do? ")
memory = [{"role": "user", "content": user_task}]
```

Your question gets stored in "memory" - this is how the AI knows what you asked.

### 5. **AI Makes a Decision**

```python
response = completion(
    model=DEFAULT_MODEL,
    messages=messages,
    tools=tools,
    max_tokens=1024
)
```

The AI looks at your question and the available tools, then decides which tool to use.

### 6. **Running the Tool**

```python
tool_name = tool.function.name
tool_args = json.loads(tool.function.arguments)
result = tool_functions[tool_name](**tool_args)
```

The AI tells us which function to run and with what arguments. We then execute it and get the result.

## Key Concepts for Beginners

### What is Function Calling?

Instead of the AI just giving you text answers, it can actually **call functions** in your code. This makes AI assistants much more powerful!

### Why Use This?

- **Automation**: AI can perform actions (read files, search databases, etc.)
- **Intelligence**: AI decides which function to use based on context
- **Flexibility**: You can add more tools easily

## Setup Instructions

### 1. Install Requirements

```bash
pip install -r requirements.txt
```

### 2. Create a `.env` File

Create a file named `.env` in the same folder:

```
DEFAULT_MODEL=gemini/gemini-1.5-flash
GEMINI_API_KEY=your_api_key_here
```

### 3. Run the Script

```bash
python LLMFunctionCall.py
```

## Example Usage

**Input:** "What files are in this directory?"

```
Tool Name: list_files
Tool Arguments: {}
Result: ['script.py', 'data.txt', 'README.md']
```

**Input:** "Read the README.md file"

```
Tool Name: read_file
Tool Arguments: {'file_name': 'README.md'}
Result: [contents of README.md]
```

## How to Extend This

Want to add more tools? Follow this pattern:

### Step 1: Create the Function

```python
def get_current_time():
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%I:%M %p")
```

### Step 2: Add to tool_functions Dictionary

```python
tool_functions = {
    "list_files": list_files,
    "read_file": read_file,
    "get_current_time": get_current_time  # Add this
}
```

### Step 3: Add Tool Description

```python
{
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "Returns the current time",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }
}
```

Now the AI can tell you the time when you ask!

## Common Issues

**"GEMINI_API_KEY not found"**

- Make sure your `.env` file exists and has your API key

**"ModuleNotFoundError"**

- Run `pip install -r requirements.txt`

**"File not found" errors**

- Make sure you're in the correct directory when running the script

## Learning Resources

- **LiteLLM Documentation**: [docs.litellm.ai](https://docs.litellm.ai)
- **Function Calling Guide**: Learn how AI models can call functions
