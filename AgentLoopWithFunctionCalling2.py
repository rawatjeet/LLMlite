try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    raise RuntimeError("Missing dependency: python-dotenv. Run 'python -m pip install -r requirements.txt' in your virtual environment.")

import os
import json
import argparse
import time
from litellm import completion
from litellm import exceptions as litellm_exceptions

# Load environment variables from .env file
load_dotenv()

# Read API key
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Make sure it's in your .env file!")

from litellm import completion
from typing import List, Dict


def list_files(path: str = ".") -> List[str]:
    """List files in the provided directory path (defaults to current dir).

    Returns an error string inside a list if path is invalid.
    """
    try:
        return os.listdir(path)
    except Exception as e:
        return [f"Error: {str(e)}"]

def read_file(file_name: str) -> str:
    """Read a file's contents."""
    try:
        with open(file_name, "r") as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: {file_name} not found."
    except Exception as e:
        return f"Error: {str(e)}"

def terminate(message: str) -> None:
    """Terminate the agent loop and provide a summary message."""
    print(f"Termination message: {message}")


def read_all_files(directory: str) -> Dict[str, str]:
    """Read all files in a directory and return a mapping filename -> content.

    Only reads regular files (not directories). Returns error messages for unreadable files.
    """
    out: Dict[str, str] = {}
    try:
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        out[name] = f.read()
                except Exception as e:
                    out[name] = f"Error reading file: {e}"
        return out
    except Exception as e:
        return {"error": str(e)}

tool_functions = {
    "list_files": list_files,
    "read_file": read_file,
    "terminate": terminate,
    "read_all_files": read_all_files
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Returns a list of files in the directory.",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the content of a specified file in the directory.",
            "parameters": {
                "type": "object",
                "properties": {"file_name": {"type": "string"}},
                "required": ["file_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_all_files",
            "description": "Reads all files in a directory and returns a mapping filename->content.",
            "parameters": {
                "type": "object",
                "properties": {"directory": {"type": "string"}},
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "terminate",
            "description": "Terminates the conversation. No further actions or interactions are possible after this. Prints the provided message for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                },
                "required": ["message"]
            }
        }
    }
]

agent_rules = [{
    "role": "system",
    "content": """
You are an AI agent that can perform tasks by using available tools.

If a user asks about files, documents, or content, first list the files before reading them.

When you are done, terminate the conversation by using the "terminate" tool and I will provide the results to the user.
"""
}]

# Initialize agent parameters
iterations = 0
max_iterations = 10

# CLI args: support --mock and optional --task to run non-interactively
parser = argparse.ArgumentParser()
parser.add_argument('--mock', action='store_true', help='Run in mock mode without calling the LLM')
parser.add_argument('--task', type=str, help='Optional task string to run (bypass interactive prompt)')
args = parser.parse_args()

if args.task:
    user_task = args.task
else:
    user_task = input("What would you like me to do? ")

memory = [{"role": "user", "content": user_task}]

def summarize_file_content(name: str, content: str) -> str:
    """Return a one-line summary for a file's content using simple heuristics."""
    if not content:
        return f"{name}: (empty)"
    s = content.strip()
    # prefer first non-empty line
    first_line = next((ln for ln in s.splitlines() if ln.strip()), '')
    if name.lower().endswith('.md') or first_line.startswith('#'):
        # markdown - use first header or first line
        return f"{name}: Markdown - {first_line}" if first_line else f"{name}: Markdown file"
    if name.lower().endswith('.log') or name.lower().endswith('.txt'):
        # text/log - show first line or short excerpt
        excerpt = first_line if first_line else (s[:120].replace('\n', ' '))
        return f"{name}: {excerpt}"
    # default: show short excerpt
    excerpt = first_line if first_line else (s[:120].replace('\n', ' '))
    return f"{name}: {excerpt}"


# The Agent Loop
while iterations < max_iterations:

    messages = agent_rules + memory


    # # If mock mode is enabled, bypass the LLM and perform heuristic actions
    # if args.mock:
    #     task = user_task.lower()
    #     # handle list files
    #     if 'list' in task and 'file' in task:
    #         path = '.'
    #         # try to detect 'in <dir>' phrase
    #         import re as _re
    #         m = _re.search(r'in\s+([\w\\/\.-]+)', user_task, flags=_re.IGNORECASE)
    #         if m:
    #             path = m.group(1)
    #         files = list_files(path)
    #         print('Mock mode - files:')
    #         for f in files:
    #             print(' -', f)
    #         break
    #     # handle read all files
    #     if 'read all' in task or 'read each' in task or ('read' in task and 'files' in task):
    #         import re as _re
    #         m = _re.search(r'in\s+([\w\\/\.-]+)', user_task, flags=_re.IGNORECASE)
    #         directory = m.group(1) if m else '.'
    #         contents = read_all_files(directory)
    #         if isinstance(contents, dict) and 'error' in contents:
    #             print('Mock mode error:', contents['error'])
    #             break
    #         print(f"Mock mode - reading files in: {directory}")
    #         for name, content in contents.items():
    #             summary = summarize_file_content(name, content)
    #             print(summary)
    #         break
    #     # fallback: echo the task
    #     print('Mock mode - echoing task:')
    #     print(user_task)
    #     break

    response = completion(
        model=DEFAULT_MODEL,
        messages=messages,
        tools=tools,
        max_tokens=1024
    )

    if response.choices[0].message.tool_calls:
        tool = response.choices[0].message.tool_calls[0]
        tool_name = tool.function.name
        tool_args = json.loads(tool.function.arguments)

        action = {
            "tool_name": tool_name,
            "args": tool_args
        }

        if tool_name == "terminate":
            print(f"Termination message: {tool_args['message']}")
            break
        elif tool_name in tool_functions:
            try:
                result = {"result": tool_functions[tool_name](**tool_args)}
            except Exception as e:
                result = {"error":f"Error executing {tool_name}: {str(e)}"}
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        print(f"Executing: {tool_name} with args {tool_args}")
        print(f"Result: {result}")
        memory.extend([
            {"role": "assistant", "content": json.dumps(action)},
            {"role": "user", "content": json.dumps(result)}
        ])
    else:
        result = response.choices[0].message.content
        print(f"Response: {result}")
        break
