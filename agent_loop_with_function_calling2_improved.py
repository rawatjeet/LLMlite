"""
Enhanced Agent with Batch Operations

This extends the simple function calling agent with:
- Batch file reading capability
- Mock mode for testing without API calls
- CLI task specification
- Enhanced file operations
- Better error handling

Use this when you need more sophisticated file operations
than the basic agent provides.
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
from typing import List, Dict, Any, Callable, Optional
from litellm import completion

# Load environment variables
load_dotenv()

# Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_ITERATIONS = int(os.getenv("DEFAULT_MAX_ITERATIONS", "10"))


# ============================================================================
# ENHANCED TOOL FUNCTIONS
# ============================================================================

def list_files(path: str = ".") -> List[str]:
    """
    List all files in a directory.
    
    Enhanced to accept custom paths.
    
    Args:
        path: Directory path to list (default: current)
    
    Returns:
        List of filenames or error message
    """
    try:
        directory = Path(path)
        if not directory.exists():
            return [f"Error: Directory '{path}' not found"]
        
        if not directory.is_dir():
            return [f"Error: '{path}' is not a directory"]
        
        items = [item.name for item in directory.iterdir() if item.is_file()]
        return sorted(items)
        
    except Exception as e:
        return [f"Error listing files: {str(e)}"]


def read_file(file_name: str) -> str:
    """
    Read contents of a single file.
    
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


def read_all_files(directory: str = ".") -> Dict[str, str]:
    """
    Read all files in a directory at once.
    
    This is more efficient than reading files one by one
    when you need to process multiple files.
    
    Args:
        directory: Directory path (default: current)
    
    Returns:
        Dictionary mapping filename to contents
    """
    result: Dict[str, str] = {}
    
    try:
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return {"error": f"Directory '{directory}' not found"}
        
        if not dir_path.is_dir():
            return {"error": f"'{directory}' is not a directory"}
        
        # Read all files
        for item in dir_path.iterdir():
            if not item.is_file():
                continue
            
            try:
                # Check size before reading
                size_mb = item.stat().st_size / (1024 * 1024)
                if size_mb > 10:
                    result[item.name] = f"Error: File too large ({size_mb:.1f}MB)"
                    continue
                
                # Try to read as text
                content = item.read_text(encoding='utf-8')
                result[item.name] = content
                
            except UnicodeDecodeError:
                result[item.name] = "Error: Not a text file"
            except Exception as e:
                result[item.name] = f"Error: {str(e)}"
        
        if not result:
            return {"info": "No files found in directory"}
        
        return result
        
    except Exception as e:
        return {"error": f"Error reading directory: {str(e)}"}


def search_files(pattern: str, directory: str = ".") -> List[str]:
    """
    Search for files matching a glob pattern.
    
    Args:
        pattern: Glob pattern (e.g., "*.py", "test_*")
        directory: Directory to search (default: current)
    
    Returns:
        List of matching filenames
    """
    try:
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return [f"Error: Directory '{directory}' not found"]
        
        matches = [p.name for p in dir_path.glob(pattern) if p.is_file()]
        
        if not matches:
            return [f"No files found matching '{pattern}' in '{directory}'"]
        
        return sorted(matches)
        
    except Exception as e:
        return [f"Error searching files: {str(e)}"]


def terminate(message: str) -> str:
    """
    Terminate the agent with a summary.
    
    Args:
        message: Summary for the user
    
    Returns:
        Formatted termination message
    """
    return f"AGENT SUMMARY:\n{message}"


# ============================================================================
# TOOL REGISTRY
# ============================================================================

TOOL_FUNCTIONS: Dict[str, Callable] = {
    "list_files": list_files,
    "read_file": read_file,
    "read_all_files": read_all_files,
    "search_files": search_files,
    "terminate": terminate,
}


TOOLS: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists all files in the specified directory. "
                          "Returns a list of filenames (not including subdirectories).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
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
            "description": "Reads and returns the complete contents of a single text file. "
                          "For reading multiple files at once, use read_all_files instead.",
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
            "name": "read_all_files",
            "description": "Reads ALL files in a directory at once and returns a mapping of "
                          "filename to contents. More efficient than reading files individually "
                          "when you need to process multiple files. Use this when the task requires "
                          "analyzing or reading multiple files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory path to read from (default: current directory)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Searches for files matching a glob pattern. "
                          "Examples: '*.py' for Python files, 'test_*' for files starting with 'test_', "
                          "'*.txt' for text files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern to match (e.g., '*.py', 'data_*.json')"
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
            "description": "Terminates the agent loop and provides a final comprehensive summary. "
                          "Use this ONLY when the task is complete. After calling this, "
                          "no further actions are possible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Comprehensive summary of what was accomplished, "
                                     "including key findings and results"
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

SYSTEM_PROMPT = """You are an efficient AI agent that can perform file operations using available tools.

IMPORTANT GUIDELINES:
1. When asked about files or directories, first list them to see what's available
2. Use read_all_files when you need to read multiple files - it's much more efficient than reading files one by one
3. Use search_files when looking for specific file types or patterns
4. Read individual files only when you need just one specific file
5. When you have completed the task, use the "terminate" tool with a comprehensive summary
6. Be thorough but efficient - minimize the number of tool calls needed
7. If you encounter errors, explain them and try alternative approaches

EFFICIENCY TIP: If a task requires reading multiple files, use read_all_files instead of 
reading files individually. This reduces the number of iterations and completes tasks faster.
"""


# ============================================================================
# AGENT EXECUTION
# ============================================================================

def execute_tool(
    tool_name: str,
    tool_args: Dict,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Execute a tool function with arguments.
    
    Args:
        tool_name: Name of tool to execute
        tool_args: Arguments for the tool
        verbose: Whether to print debug info
    
    Returns:
        Result dictionary with 'result' or 'error'
    """
    if tool_name == "terminate":
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


def format_result_summary(result_data: Any) -> str:
    """
    Create a concise summary of a result for display.
    
    Args:
        result_data: The result to summarize
    
    Returns:
        Human-readable summary string
    """
    if isinstance(result_data, dict):
        if "error" in result_data:
            return f"Error: {result_data['error']}"
        
        file_count = len([k for k in result_data.keys() if k not in ["error", "info"]])
        if file_count > 0:
            return f"{file_count} files read"
        return str(result_data)
    
    elif isinstance(result_data, list):
        return f"{len(result_data)} items"
    
    elif isinstance(result_data, str):
        if len(result_data) > 100:
            return f"{len(result_data)} characters"
        return result_data
    
    return str(result_data)


def run_agent(
    task: str,
    model: str = DEFAULT_MODEL,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    verbose: bool = False
) -> None:
    """
    Run the enhanced agent loop.
    
    Args:
        task: User's task
        model: LLM model to use
        max_iterations: Maximum iterations
        verbose: Show detailed output
    """
    print("\n" + "=" * 70)
    print("🤖 ENHANCED AGENT WITH BATCH OPERATIONS")
    print("=" * 70)
    print(f"\n📋 Task: {task}")
    print(f"🔧 Tools: {', '.join(TOOL_FUNCTIONS.keys())}")
    print(f"🔄 Max iterations: {max_iterations}\n")
    
    # Initialize conversation
    memory = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task}
    ]
    
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        print(f"{'─' * 70}")
        print(f"Iteration {iteration}/{max_iterations}")
        print(f"{'─' * 70}")
        
        # Call LLM
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
        
        # Check for tool call
        if not response.choices[0].message.tool_calls:
            text_response = response.choices[0].message.content
            print(f"💬 Agent response: {text_response}")
            break
        
        # Extract tool call
        tool_call = response.choices[0].message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        
        print(f"🔧 Tool: {tool_name}")
        if tool_args:
            args_display = ", ".join(f"{k}={repr(v)[:50]}" for k, v in tool_args.items())
            print(f"   Args: {args_display}")
        
        # Execute tool
        result = execute_tool(tool_name, tool_args, verbose=verbose)
        
        # Display result
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            result_data = result["result"]
            summary = format_result_summary(result_data)
            print(f"✅ Result: {summary}")
            
            # Show details in verbose mode
            if verbose:
                if isinstance(result_data, dict) and len(result_data) <= 5:
                    print("   Details:")
                    for key, value in result_data.items():
                        value_preview = str(value)[:100]
                        print(f"     {key}: {value_preview}...")
                elif isinstance(result_data, list) and len(result_data) <= 10:
                    print("   Items:")
                    for item in result_data:
                        print(f"     • {item}")
        
        # Check termination
        if result.get("terminated"):
            print("\n" + "=" * 70)
            print("✅ AGENT COMPLETED TASK")
            print("=" * 70)
            break
        
        # Update memory
        action_summary = {"tool_name": tool_name, "args": tool_args}
        memory.extend([
            {"role": "assistant", "content": json.dumps(action_summary)},
            {"role": "user", "content": json.dumps(result)}
        ])
    
    if iteration >= max_iterations:
        print("\n" + "=" * 70)
        print("⚠️  MAXIMUM ITERATIONS REACHED")
        print("=" * 70)
        print("The agent may not have completed the task.")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def validate_api_key():
    """Validate API key presence."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not gemini_key and not openai_key:
        print("❌ No API key found!")
        print("\nPlease set one in your .env file:")
        print("  GEMINI_API_KEY=your-key")
        print("  or")
        print("  OPENAI_API_KEY=your-key")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced agent with batch file operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python agent_loop_with_function_calling2.py
  
  # Specify task directly
  python agent_loop_with_function_calling2.py --task "Read all Python files"
  
  # Verbose output
  python agent_loop_with_function_calling2.py --task "Analyze files" --verbose
  
  # Custom model
  python agent_loop_with_function_calling2.py --model openai/gpt-4

Example Tasks:
  - "Read all files in the current directory"
  - "Find all Python files and summarize their purpose"
  - "Analyze all .txt files and create a summary"
  - "Read all markdown files and list their headings"
        """
    )
    
    parser.add_argument(
        '--task',
        type=str,
        help='Task for the agent (prompts if not provided)'
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
    
    # Get task
    if args.task:
        task = args.task
    else:
        print("\n" + "=" * 70)
        print("🤖 ENHANCED AGENT WITH BATCH OPERATIONS")
        print("=" * 70)
        print("\nWhat would you like me to do?")
        print("\nExample tasks:")
        print("  • Read all files in this directory")
        print("  • Find Python files and summarize each")
        print("  • Analyze all .txt files")
        print("\n💡 Your task: ", end="")
        
        task = input().strip()
        
        if not task:
            print("❌ No task provided. Exiting.")
            return 1
    
    try:
        # Run agent
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
