"""
AI Agent with Tool Calling

A true autonomous agent that can:
- Make decisions about which tools to use
- Execute Python functions (tools) based on user requests
- Maintain conversation memory across multiple steps
- Loop until task completion

This demonstrates the core concepts of agentic AI systems.
"""

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    raise RuntimeError(
        "Missing dependency: python-dotenv\n"
        "Install it by running: pip install -r requirements.txt"
    )

import os
import json
import argparse
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from litellm import completion
from litellm import exceptions as litellm_exceptions

# Load environment variables
load_dotenv()

# Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_ITERATIONS = int(os.getenv("DEFAULT_MAX_ITERATIONS", "10"))
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "1024"))


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def extract_markdown_block(response: str, block_type: str = "json") -> str:
    """
    Extract content from markdown code blocks.
    
    The LLM often wraps responses in markdown like:
    ```json
    {"key": "value"}
    ```
    
    This function extracts just the content.
    
    Args:
        response: The raw LLM response
        block_type: The type of code block to extract (e.g., "json", "action")
    
    Returns:
        The extracted content without markdown formatting
    """
    if '```' not in response:
        return response.strip()
    
    parts = response.split('```')
    if len(parts) < 2:
        return response.strip()
    
    code_block = parts[1].strip()
    
    # Remove language identifier
    if code_block.lower().startswith(block_type):
        code_block = code_block[len(block_type):].strip()
    
    return code_block


def safe_json_parse(text: str) -> Optional[Dict]:
    """
    Safely parse JSON with error handling.
    
    Args:
        text: The text to parse as JSON
    
    Returns:
        Parsed dictionary or None if parsing fails
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parse error: {e}")
        return None


# ============================================================================
# LLM INTERACTION
# ============================================================================

def generate_response(
    messages: List[Dict],
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    verbose: bool = False
) -> str:
    """
    Generate a response from the LLM.
    
    Args:
        messages: List of conversation messages
        model: Model identifier
        max_tokens: Maximum tokens in response
        verbose: Whether to print debug info
    
    Returns:
        The generated response text
    """
    if verbose:
        print(f"🔄 Calling LLM ({model})...")
    
    try:
        response = completion(
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Error calling LLM: {e}")
        raise


def parse_action(response: str, verbose: bool = False) -> Dict:
    """
    Parse the LLM response into a structured action dictionary.
    
    Expected format:
    ```action
    {
        "tool_name": "read_file",
        "args": {"file_name": "example.txt"}
    }
    ```
    
    Args:
        response: The raw LLM response
        verbose: Whether to print debug info
    
    Returns:
        Dictionary with 'tool_name' and 'args' keys
    """
    try:
        # Extract the action block
        action_text = extract_markdown_block(response, "action")
        
        # Parse JSON
        action_json = safe_json_parse(action_text)
        
        if not action_json:
            return {
                "tool_name": "error",
                "args": {"message": "Failed to parse action JSON"}
            }
        
        # Validate required fields
        if "tool_name" not in action_json or "args" not in action_json:
            return {
                "tool_name": "error",
                "args": {
                    "message": "Action must contain 'tool_name' and 'args' fields"
                }
            }
        
        if verbose:
            print(f"✓ Parsed action: {action_json['tool_name']}")
        
        return action_json
        
    except Exception as e:
        return {
            "tool_name": "error",
            "args": {"message": f"Error parsing action: {str(e)}"}
        }


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

def list_files(directory: str = ".") -> List[str]:
    """
    List files in a directory.
    
    Args:
        directory: Directory path to list (default: current directory)
    
    Returns:
        List of file and directory names
    """
    try:
        path = Path(directory)
        if not path.exists():
            return [f"Error: Directory '{directory}' not found"]
        
        items = [item.name for item in path.iterdir()]
        return sorted(items)
    except Exception as e:
        return [f"Error listing files: {str(e)}"]


def read_file(file_name: str) -> str:
    """
    Read the contents of a file.
    
    Args:
        file_name: Name or path of the file to read
    
    Returns:
        File contents as a string, or error message
    """
    try:
        path = Path(file_name)
        if not path.exists():
            return f"Error: File '{file_name}' not found"
        
        if not path.is_file():
            return f"Error: '{file_name}' is not a file"
        
        # Check file size to avoid reading huge files
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > 10:
            return f"Error: File too large ({size_mb:.1f} MB). Maximum 10 MB."
        
        return path.read_text(encoding='utf-8')
        
    except UnicodeDecodeError:
        return f"Error: Cannot read '{file_name}' - not a text file"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(file_name: str, content: str) -> str:
    """
    Write content to a file.
    
    Args:
        file_name: Name of the file to write
        content: Content to write to the file
    
    Returns:
        Success message or error
    """
    try:
        path = Path(file_name)
        path.write_text(content, encoding='utf-8')
        return f"Successfully wrote {len(content)} characters to '{file_name}'"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def search_files(pattern: str, directory: str = ".") -> List[str]:
    """
    Search for files matching a pattern.
    
    Args:
        pattern: Glob pattern to search for (e.g., "*.py", "test_*")
        directory: Directory to search in
    
    Returns:
        List of matching file paths
    """
    try:
        path = Path(directory)
        if not path.exists():
            return [f"Error: Directory '{directory}' not found"]
        
        matches = [str(p.relative_to(path)) for p in path.glob(pattern)]
        return sorted(matches) if matches else ["No files found matching pattern"]
        
    except Exception as e:
        return [f"Error searching files: {str(e)}"]


# Tool registry - maps tool names to their functions
TOOLS: Dict[str, Callable] = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "search_files": search_files,
}


# Tool schemas for the agent's knowledge
TOOL_SCHEMAS = {
    "list_files": {
        "description": "Lists all files and directories in the specified directory.",
        "parameters": {
            "directory": {
                "type": "string",
                "description": "The directory path to list (default: current directory)",
                "optional": True
            }
        }
    },
    "read_file": {
        "description": "Reads and returns the content of a text file.",
        "parameters": {
            "file_name": {
                "type": "string",
                "description": "The name or path of the file to read"
            }
        }
    },
    "write_file": {
        "description": "Writes content to a file, creating or overwriting it.",
        "parameters": {
            "file_name": {
                "type": "string",
                "description": "The name of the file to write"
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file"
            }
        }
    },
    "search_files": {
        "description": "Searches for files matching a glob pattern (e.g., '*.py', 'test_*').",
        "parameters": {
            "pattern": {
                "type": "string",
                "description": "The glob pattern to match files against"
            },
            "directory": {
                "type": "string",
                "description": "The directory to search in (default: current directory)",
                "optional": True
            }
        }
    },
    "terminate": {
        "description": "Ends the agent loop and provides a final summary to the user.",
        "parameters": {
            "message": {
                "type": "string",
                "description": "Summary message explaining what was accomplished"
            }
        }
    }
}


# ============================================================================
# AGENT SYSTEM PROMPT
# ============================================================================

def get_system_prompt() -> str:
    """
    Generate the system prompt that defines agent behavior.
    
    Returns:
        The complete system prompt as a string
    """
    tools_json = json.dumps(TOOL_SCHEMAS, indent=2)
    
    return f"""You are an autonomous AI agent that can perform tasks by using available tools.

Available tools:

```json
{tools_json}
```

IMPORTANT RULES:
1. Think step-by-step about what you need to do
2. Use tools strategically to accomplish the user's goal
3. If the user asks about files, first list them before reading
4. Always provide reasoning before choosing a tool
5. When you've completed the task, use the "terminate" tool with a summary
6. EVERY response MUST include an action in the specified format

RESPONSE FORMAT:
You must ALWAYS respond in this exact format:

<Your step-by-step reasoning about what to do next>

```action
{{
    "tool_name": "name_of_tool_to_use",
    "args": {{
        "param_name": "param_value"
    }}
}}
```

Example response:
"I need to first see what files are available in the directory before I can help the user find specific information."

```action
{{
    "tool_name": "list_files",
    "args": {{}}
}}
```
"""


# ============================================================================
# AGENT EXECUTION
# ============================================================================

def execute_tool(tool_name: str, args: Dict[str, Any], verbose: bool = False) -> Dict:
    """
    Execute a tool with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        args: Dictionary of arguments for the tool
        verbose: Whether to print debug info
    
    Returns:
        Dictionary with 'result' or 'error' key
    """
    if tool_name == "terminate":
        return {"result": "Agent terminated", "terminate": True}
    
    if tool_name == "error":
        return {"error": args.get("message", "Unknown error")}
    
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}
    
    try:
        if verbose:
            print(f"🔧 Executing: {tool_name}({args})")
        
        tool_func = TOOLS[tool_name]
        result = tool_func(**args)
        
        return {"result": result}
        
    except TypeError as e:
        return {"error": f"Invalid arguments for {tool_name}: {str(e)}"}
    except Exception as e:
        return {"error": f"Error executing {tool_name}: {str(e)}"}


def run_agent(
    task: str,
    model: str = DEFAULT_MODEL,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    verbose: bool = False
) -> str:
    """
    Run the agent loop to complete a task.
    
    This is the main agent execution function that:
    1. Maintains conversation memory
    2. Generates responses from the LLM
    3. Parses and executes tool calls
    4. Loops until completion or max iterations
    
    Args:
        task: The user's task description
        model: LLM model to use
        max_iterations: Maximum number of agent steps
        verbose: Whether to print detailed progress
    
    Returns:
        The final summary message from the agent
    """
    print("\n" + "=" * 70)
    print("🤖 AI AGENT WITH TOOL CALLING")
    print("=" * 70)
    print(f"\n📋 Task: {task}")
    print(f"🔧 Available tools: {', '.join(TOOLS.keys())}")
    print(f"🔄 Max iterations: {max_iterations}")
    print("\n" + "-" * 70)
    
    # Initialize agent memory
    system_prompt = get_system_prompt()
    memory = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task}
    ]
    
    iteration = 0
    
    # Main agent loop
    while iteration < max_iterations:
        iteration += 1
        
        print(f"\n🔄 Iteration {iteration}/{max_iterations}")
        print("-" * 70)
        
        # Step 1: Generate response from LLM
        print("🧠 Agent thinking...")
        try:
            response = generate_response(memory, model=model, verbose=verbose)
        except Exception as e:
            print(f"❌ Failed to generate response: {e}")
            return "Agent failed due to LLM error"
        
        if verbose:
            print(f"\n📝 Full response:\n{response}\n")
        else:
            # Show just the reasoning part (before the action)
            reasoning = response.split("```")[0].strip()
            print(f"💭 Reasoning: {reasoning[:200]}...")
        
        # Step 2: Parse the action
        action = parse_action(response, verbose=verbose)
        tool_name = action["tool_name"]
        tool_args = action["args"]
        
        print(f"🔧 Action: {tool_name}")
        if tool_args:
            print(f"   Args: {tool_args}")
        
        # Step 3: Execute the tool
        result = execute_tool(tool_name, tool_args, verbose=verbose)
        
        # Step 4: Display result
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Result: ", end="")
            result_data = result.get("result", "")
            if isinstance(result_data, list):
                print(f"{len(result_data)} items")
                if verbose:
                    for item in result_data[:10]:
                        print(f"   - {item}")
                    if len(result_data) > 10:
                        print(f"   ... and {len(result_data) - 10} more")
            elif isinstance(result_data, str):
                if len(result_data) > 200 and not verbose:
                    print(f"{result_data[:200]}... ({len(result_data)} chars total)")
                else:
                    print(result_data)
            else:
                print(result_data)
        
        # Step 5: Check for termination
        if tool_name == "terminate":
            print("\n" + "=" * 70)
            print("✅ AGENT COMPLETED TASK")
            print("=" * 70)
            return tool_args.get("message", "Task completed")
        
        # Step 6: Update memory
        memory.extend([
            {"role": "assistant", "content": response},
            {"role": "user", "content": json.dumps(result)}
        ])
        
        # Prevent infinite loops
        if iteration >= max_iterations:
            print("\n" + "=" * 70)
            print("⚠️  MAXIMUM ITERATIONS REACHED")
            print("=" * 70)
            return "Agent reached maximum iterations without completing task"
    
    return "Agent loop completed"


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def validate_api_key():
    """Validate that an API key is configured."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not gemini_key and not openai_key:
        print("❌ No API key found!")
        print("\nPlease set one of the following in your .env file:")
        print("  - GEMINI_API_KEY=your-key-here")
        print("  - OPENAI_API_KEY=your-key-here")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="AI Agent with Tool Calling - Autonomous task execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_tools.py
  python agent_tools.py --task "Find all Python files"
  python agent_tools.py --verbose
  python agent_tools.py --max-iterations 5

Example Tasks:
  - "What Python files are in this directory?"
  - "Read the README file and summarize it"
  - "Find all test files and list them"
  - "Create a summary of all .py files"
        """
    )
    
    parser.add_argument(
        '--task',
        type=str,
        help='Task for the agent to complete (if not provided, will prompt)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default=DEFAULT_MODEL,
        help='Model to use (default: from env or gemini/gemini-1.5-flash)'
    )
    
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help='Maximum agent iterations (default: 10)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed execution information'
    )
    
    args = parser.parse_args()
    
    # Validate API key
    validate_api_key()
    
    # Get task from user if not provided
    if args.task:
        task = args.task
    else:
        print("\n" + "=" * 70)
        print("🤖 AI AGENT WITH TOOL CALLING")
        print("=" * 70)
        print("\nWhat would you like me to do?")
        print("\nExample tasks:")
        print("  - What Python files are in this directory?")
        print("  - Read the README and tell me what this project does")
        print("  - Find all files with 'test' in the name")
        print("\n💡 Your task: ", end="")
        task = input().strip()
        
        if not task:
            print("❌ No task provided. Exiting.")
            return 1
    
    try:
        # Run the agent
        final_message = run_agent(
            task=task,
            model=args.model,
            max_iterations=args.max_iterations,
            verbose=args.verbose
        )
        
        print(f"\n📊 Final Summary:\n{final_message}\n")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Agent interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Agent failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
