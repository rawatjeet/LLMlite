"""
AI Agent with Function Calling
This script creates an AI agent that can use tools (functions) to perform tasks.
Perfect for beginners learning about AI function calling!
"""

# Import required libraries
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    raise RuntimeError(
        "Missing dependency: python-dotenv. "
        "Run 'pip install -r requirements.txt' in your virtual environment."
    )

import os
import json
from litellm import completion

# Load environment variables from .env file
load_dotenv()

# Read configuration from environment variables
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Make sure it's in your .env file!\n"
        "Create a .env file with: GEMINI_API_KEY=your_key_here"
    )

# ============================================
# TOOL FUNCTIONS (The AI can call these)
# ============================================

def list_files() -> list:
    """
    List all files in the current directory.
    
    Returns:
        list: A list of file names
    """
    try:
        files = os.listdir(".")
        return files
    except Exception as e:
        return [f"Error listing files: {str(e)}"]


def read_file(file_name: str) -> str:
    """
    Read the contents of a file.
    
    Args:
        file_name (str): The name of the file to read
        
    Returns:
        str: The file contents or an error message
    """
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: File '{file_name}' not found."
    except PermissionError:
        return f"Error: Permission denied to read '{file_name}'."
    except Exception as e:
        return f"Error reading file: {str(e)}"


# Dictionary mapping function names to actual functions
# The AI will call these by name
tool_functions = {
    "list_files": list_files,
    "read_file": read_file
}

# ============================================
# TOOL DEFINITIONS (Tell the AI about tools)
# ============================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Returns a list of all files in the current directory.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads and returns the content of a specified file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The name of the file to read"
                    }
                },
                "required": ["file_name"]
            }
        }
    }
]

# ============================================
# AGENT INSTRUCTIONS
# ============================================

agent_rules = [{
    "role": "system",
    "content": """
You are a helpful AI assistant that can interact with files.

When a user asks about files or documents:
1. First use list_files() to see what files are available
2. Then use read_file() to read specific files if needed

Always be helpful and explain what you're doing.
"""
}]

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Main function to run the AI agent."""
    
    print("=" * 50)
    print("AI File Assistant")
    print("=" * 50)
    print("I can help you list and read files!")
    print("Examples:")
    print("  - 'What files are here?'")
    print("  - 'Read the README.md file'")
    print("  - 'Show me all Python files'")
    print("=" * 50)
    
    # Get user input
    user_task = input("\nWhat would you like me to do? ")
    
    if not user_task.strip():
        print("No task provided. Exiting.")
        return
    
    # Create conversation memory
    memory = [{"role": "user", "content": user_task}]
    messages = agent_rules + memory
    
    try:
        # Call the AI with available tools
        print("\n🤖 Thinking...")
        response = completion(
            model=DEFAULT_MODEL,
            messages=messages,
            tools=tools,
            max_tokens=1024
        )
        
        # Check if the AI wants to use a tool
        if not response.choices[0].message.tool_calls:
            print("\n❌ The AI didn't call any tools.")
            print(f"Response: {response.choices[0].message.content}")
            return
        
        # Extract tool information
        tool = response.choices[0].message.tool_calls[0]
        tool_name = tool.function.name
        tool_args = json.loads(tool.function.arguments)
        
        print(f"\n🔧 Using tool: {tool_name}")
        if tool_args:
            print(f"📋 Arguments: {tool_args}")
        
        # Execute the tool
        result = tool_functions[tool_name](**tool_args)
        
        # Display results
        print("\n" + "=" * 50)
        print("RESULT:")
        print("=" * 50)
        print(result)
        print("=" * 50)
        
    except KeyError as e:
        print(f"\n❌ Error: Unknown tool '{e}' requested by AI")
    except json.JSONDecodeError:
        print("\n❌ Error: Could not parse tool arguments")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()