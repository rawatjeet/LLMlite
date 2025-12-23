"""
Simple Agent with Native Function Calling

This demonstrates the simplest form of an agent using LLM's native
function calling capability. The LLM directly selects and invokes tools
without custom parsing logic.

Key Features:
- Uses native LLM function calling (not custom JSON parsing)
- Simple and reliable
- Easy to understand
- Production-ready
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
import sys
from pathlib import Path
from typing import List, Dict, Any, Callable
from litellm import completion
from litellm import exceptions as litellm_exceptions

# Load environment variables
load_dotenv()

# Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_ITERATIONS = int(os.getenv("DEFAULT_MAX_ITERATIONS", "10"))


# ============================================================================
# TOOL FUNCTIONS
# ============================================================================

def list_files(directory: str = ".") -> List[str]:
    """
    List all files in a directory.
    
    Args:
        directory: Path to directory (default: current)
    
    Returns:
        List of filenames, or error message in list
    """
    try:
        path = Path(directory)
        if not path.exists():
            return [f"Error: Directory '{directory}' not found"]
        
        items = [item.name for item in path.iterdir() if item.is_file()]
        return sorted(items)
    except Exception as e:
        return [f"Error listing files: {str(e)}"]


def read_file(file_name: str) -> str:
    """
    Read contents of a file.
    
    Args:
        file_name: Name or path of file to read
    
    Returns:
        File contents or error message
    """
    try:
        path = Path(file_name)
        
        if not path.exists():
            return f"Error: File '{file_name}' not found"
        
        if not path.is_file():
            return f"Error: '{file_name}' is not a file"
        
        # Check file size (limit to 10MB)
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > 10:
            return f"Error: File too large ({size_mb:.1f}MB). Max 10MB"
        
        return path.read_text(encoding='utf-8')
        
    except UnicodeDecodeError:
        return f"Error: Cannot read '{file_name}' - not a text file"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def search_files(pattern: str, directory: str = ".") -> List[str]:
    """
    Search for files matching a pattern.
    
    Args:
        pattern: Glob pattern (e.g., "*.py", "test_*")
        directory: Directory to search (default: current)
    
    Returns:
        List of matching files or error message
    """
    try:
        path = Path(directory)
        if not path.exists():
            return [f"Error: Directory '{directory}' not found"]
        
        matches = [str(p.name) for p in path.glob(pattern) if p.is_file()]
        
        if not matches:
            return [f"No files found matching '{pattern}' in '{directory}'"]
        
        return sorted(matches)
        
    except Exception as e:
        return [f"Error searching files: {str(e)}"]


def terminate(message: str) -> str:
    """
    Terminate the agent loop with a summary.
    
    Args:
        message: Summary message for the user
    
    Returns:
        Formatted termination message
    """
    return f"AGENT SUMMARY:\n{message}"


# ============================================================================
# TOOL REGISTRY
# ============================================================================

# Map tool names to their implementations
TOOL_FUNCTIONS: Dict[str, Callable] = {
    "list_files": list_files,
    "read_file": read_file,
    "search_files": search_files,
    "terminate": terminate,
}


# Tool definitions for the LLM
TOOLS: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists all files in the specified directory. Returns a list of filenames.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory path to list (default: current directory)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads and returns the complete contents of a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "Name or path of the file to read"
                    }
                },
                "required": ["file_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Searches for files matching a glob pattern (e.g., '*.py', 'test_*').",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern to match files (e.g., '*.txt', 'data_*')"
                    },
                    "directory": {
                        "type": "string",
                        "description": "Directory to search in (default: current directory)"
                    }
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "terminate",
            "description": "Terminates the agent loop and provides a final summary. "
                          "Use this when the task is complete. No further actions "
                          "are possible after calling this.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Comprehensive summary of what was accomplished"
                    }
                },
                "required": ["message"]
            }
        }
    }
]


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """You are an AI agent that can perform tasks by using available tools.

IMPORTANT GUIDELINES:
1. If the user asks about files or directories, first list them to see what's available
2. Use search_files when looking for specific file types or patterns
3. Read files one at a time to understand their contents
4. When you have completed the task, use the "terminate" tool with a comprehensive summary
5. Be thorough and systematic in your approach
6. If you encounter errors, explain them and try alternative approaches

Available tools will be provided to you automatically.
"""


# ============================================================================
# AGENT EXECUTION
# ============================================================================

def execute_tool(tool_name: str, tool_args: Dict, verbose: bool = False) -> Dict:
    """
    Execute a tool function with given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        tool_args: Dictionary of arguments
        verbose: Whether to print debug info
    
    Returns:
        Result dictionary with 'result' or 'error' key
    """
    if tool_name == "terminate":
        # Special handling for terminate
        result = TOOL_FUNCTIONS["terminate"](**tool_args)
        return {"result": result, "terminated": True}
    
    if tool_name not in TOOL_FUNCTIONS:
        return {"error": f"Unknown tool: {tool_name}"}
    
    try:
        if verbose:
            print(f"   Executing: {tool_name}({tool_args})")
        
        result = TOOL_FUNCTIONS[tool_name](**tool_args)
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
) -> None:
    """
    Run the agent loop with native function calling.
    
    This is simpler than custom parsing because:
    - LLM handles tool selection natively
    - No need to parse JSON manually
    - More reliable and robust
    
    Args:
        task: User's task description
        model: LLM model to use
        max_iterations: Maximum loop iterations
        verbose: Whether to print detailed output
    """
    print("\n" + "=" * 70)
    print("🤖 SIMPLE AGENT WITH NATIVE FUNCTION CALLING")
    print("=" * 70)
    print(f"\n📋 Task: {task}")
    print(f"🔧 Available tools: {len(TOOL_FUNCTIONS)}")
    print(f"🔄 Max iterations: {max_iterations}\n")
    
    # Initialize conversation memory
    memory = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task}
    ]
    
    iteration = 0
    
    # Main agent loop
    while iteration < max_iterations:
        iteration += 1
        
        print(f"{'─' * 70}")
        print(f"Iteration {iteration}/{max_iterations}")
        print(f"{'─' * 70}")
        
        # Call LLM with function calling
        print("🧠 Agent thinking...")
        
        try:
            response = completion(
                model=model,
                messages=memory,
                tools=TOOLS,
                max_tokens=1024
            )
        except Exception as e:
            print(f"❌ Error calling LLM: {e}")
            break
        
        # Check if LLM wants to call a function
        if not response.choices[0].message.tool_calls:
            # No tool call - just text response
            text_response = response.choices[0].message.content
            print(f"💬 Agent response: {text_response}")
            break
        
        # Extract tool call information
        tool_call = response.choices[0].message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        
        print(f"🔧 Tool: {tool_name}")
        if tool_args:
            args_str = ", ".join(f"{k}={repr(v)}" for k, v in tool_args.items())
            print(f"   Args: {args_str}")
        
        # Execute the tool
        result = execute_tool(tool_name, tool_args, verbose=verbose)
        
        # Display result
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            result_data = result["result"]
            
            if isinstance(result_data, list):
                print(f"✅ Result: {len(result_data)} items")
                if verbose or len(result_data) <= 10:
                    for item in result_data:
                        print(f"   • {item}")
                elif len(result_data) > 10:
                    for item in result_data[:5]:
                        print(f"   • {item}")
                    print(f"   ... and {len(result_data) - 5} more")
            
            elif isinstance(result_data, str):
                if len(result_data) > 300 and not verbose:
                    print(f"✅ Result: {result_data[:300]}...")
                    print(f"   (Total: {len(result_data)} characters)")
                else:
                    print(f"✅ Result: {result_data}")
            else:
                print(f"✅ Result: {result_data}")
        
        # Check for termination
        if result.get("terminated"):
            print("\n" + "=" * 70)
            print("✅ AGENT COMPLETED TASK")
            print("=" * 70)
            break
        
        # Update conversation memory
        action_summary = {
            "tool_name": tool_name,
            "args": tool_args
        }
        
        memory.extend([
            {"role": "assistant", "content": json.dumps(action_summary)},
            {"role": "user", "content": json.dumps(result)}
        ])
    
    if iteration >= max_iterations:
        print("\n" + "=" * 70)
        print("⚠️  MAXIMUM ITERATIONS REACHED")
        print("=" * 70)


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
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Simple agent with native function calling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_loop_with_function_calling.py
  python agent_loop_with_function_calling.py --task "Find all Python files"
  python agent_loop_with_function_calling.py --verbose
  python agent_loop_with_function_calling.py --model openai/gpt-4

Example Tasks:
  - "What Python files are in this directory?"
  - "Read the README file"
  - "Find all files ending with .txt"
  - "List all files and tell me about them"
        """
    )
    
    parser.add_argument(
        '--task',
        type=str,
        help='Task for the agent (if not provided, will prompt)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default=DEFAULT_MODEL,
        help='LLM model to use'
    )
    
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help='Maximum agent iterations'
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
        print("🤖 SIMPLE AGENT WITH NATIVE FUNCTION CALLING")
        print("=" * 70)
        print("\nWhat would you like me to do?")
        print("\nExample tasks:")
        print("  • What Python files are in this directory?")
        print("  • Read the README and summarize it")
        print("  • Find all .txt files")
        print("\n💡 Your task: ", end="")
        
        task = input().strip()
        
        if not task:
            print("❌ No task provided. Exiting.")
            return 1
    
    try:
        # Run the agent
        run_agent(
            task=task,
            model=args.model,
            max_iterations=args.max_iterations,
            verbose=args.verbose
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Agent interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Agent failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
