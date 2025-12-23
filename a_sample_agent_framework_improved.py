"""
Advanced Agent Framework (GAME Architecture)

This implements a sophisticated agent architecture with:
- Goals: What the agent should accomplish
- Actions: What the agent can do
- Memory: What the agent remembers
- Environment: Where the agent operates

This is a production-ready framework for building complex AI agents.
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
import traceback
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional
from litellm import completion
from litellm import exceptions as litellm_exceptions

# Load environment variables
load_dotenv()

# Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_ITERATIONS = int(os.getenv("DEFAULT_MAX_ITERATIONS", "50"))


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Prompt:
    """
    Represents a complete prompt to send to the LLM.
    
    Attributes:
        messages: Conversation history
        tools: Available function calling tools
        metadata: Additional context information
    """
    messages: List[Dict] = field(default_factory=list)
    tools: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass(frozen=True)
class Goal:
    """
    Represents an agent goal with priority and description.
    
    Frozen dataclass ensures goals are immutable.
    
    Attributes:
        priority: Higher numbers = higher priority
        name: Short goal identifier
        description: Detailed goal instructions
    """
    priority: int
    name: str
    description: str


# ============================================================================
# ACTION SYSTEM
# ============================================================================

class Action:
    """
    Represents an executable action the agent can perform.
    
    Actions are the agent's capabilities - functions it can call
    to interact with the environment.
    """
    
    def __init__(
        self,
        name: str,
        function: Callable,
        description: str,
        parameters: Dict,
        terminal: bool = False,
        requires_confirmation: bool = False
    ):
        """
        Initialize an action.
        
        Args:
            name: Action identifier
            function: Python function to execute
            description: What this action does
            parameters: JSON schema for parameters
            terminal: Whether this action ends the agent loop
            requires_confirmation: Whether to ask before executing
        """
        self.name = name
        self.function = function
        self.description = description
        self.parameters = parameters
        self.terminal = terminal
        self.requires_confirmation = requires_confirmation
    
    def execute(self, **kwargs) -> Any:
        """
        Execute the action's function with given arguments.
        
        Args:
            **kwargs: Arguments to pass to the function
        
        Returns:
            The function's return value
        """
        return self.function(**kwargs)
    
    def __repr__(self) -> str:
        return f"Action(name={self.name}, terminal={self.terminal})"


class ActionRegistry:
    """
    Registry that stores and manages all available actions.
    
    This allows dynamic registration and retrieval of actions.
    """
    
    def __init__(self):
        self.actions: Dict[str, Action] = {}
    
    def register(self, action: Action) -> None:
        """
        Register a new action.
        
        Args:
            action: The action to register
        """
        self.actions[action.name] = action
    
    def get_action(self, name: str) -> Optional[Action]:
        """
        Retrieve an action by name.
        
        Args:
            name: Action name to look up
        
        Returns:
            The action if found, None otherwise
        """
        return self.actions.get(name)
    
    def get_actions(self) -> List[Action]:
        """
        Get all registered actions.
        
        Returns:
            List of all actions
        """
        return list(self.actions.values())
    
    def list_action_names(self) -> List[str]:
        """
        Get names of all registered actions.
        
        Returns:
            List of action names
        """
        return list(self.actions.keys())


# ============================================================================
# MEMORY SYSTEM
# ============================================================================

class Memory:
    """
    Manages the agent's conversation history and working memory.
    
    Memory items have a 'type' field:
    - 'user': Messages from the user
    - 'assistant': Agent's decisions/reasoning
    - 'environment': Results from action execution
    - 'system': System instructions
    """
    
    def __init__(self):
        self.items: List[Dict] = []
    
    def add_memory(self, memory: Dict) -> None:
        """
        Add a memory item.
        
        Args:
            memory: Dictionary with 'type' and 'content' keys
        """
        if "type" not in memory:
            raise ValueError("Memory must have a 'type' field")
        self.items.append(memory)
    
    def get_memories(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve memory items.
        
        Args:
            limit: Maximum number of items to return (from start)
        
        Returns:
            List of memory items
        """
        if limit is None:
            return self.items
        return self.items[:limit]
    
    def get_recent_memories(self, count: int = 10) -> List[Dict]:
        """
        Get the most recent memory items.
        
        Args:
            count: Number of recent items to return
        
        Returns:
            List of recent memory items
        """
        return self.items[-count:] if count > 0 else []
    
    def copy_without_system_memories(self) -> 'Memory':
        """
        Create a copy excluding system messages.
        
        Useful for showing conversation history without system prompts.
        
        Returns:
            New Memory object without system items
        """
        filtered_items = [m for m in self.items if m.get("type") != "system"]
        memory = Memory()
        memory.items = filtered_items
        return memory
    
    def clear(self) -> None:
        """Clear all memory items."""
        self.items = []
    
    def __len__(self) -> int:
        return len(self.items)


# ============================================================================
# ENVIRONMENT
# ============================================================================

class Environment:
    """
    Represents the environment where the agent operates.
    
    Responsible for:
    - Executing actions safely
    - Formatting results consistently
    - Handling errors gracefully
    """
    
    def execute_action(self, action: Action, args: Dict) -> Dict:
        """
        Execute an action and return formatted result.
        
        Args:
            action: The action to execute
            args: Arguments for the action
        
        Returns:
            Dictionary with execution results or error information
        """
        try:
            result = action.execute(**args)
            return self.format_result(result)
        except TypeError as e:
            return {
                "tool_executed": False,
                "error": f"Invalid arguments: {str(e)}",
                "traceback": traceback.format_exc()
            }
        except Exception as e:
            return {
                "tool_executed": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def format_result(self, result: Any) -> Dict:
        """
        Format a successful result with metadata.
        
        Args:
            result: The raw result from action execution
        
        Returns:
            Formatted result dictionary
        """
        return {
            "tool_executed": True,
            "result": result,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
        }


# ============================================================================
# AGENT LANGUAGE (COMMUNICATION PROTOCOL)
# ============================================================================

class AgentLanguage:
    """
    Base class for agent communication protocols.
    
    Defines how to:
    - Format prompts for the LLM
    - Parse LLM responses
    - Represent actions and memory
    """
    
    def construct_prompt(
        self,
        actions: List[Action],
        environment: Environment,
        goals: List[Goal],
        memory: Memory
    ) -> Prompt:
        """
        Construct a complete prompt from agent state.
        
        Args:
            actions: Available actions
            environment: The environment
            goals: Agent goals
            memory: Conversation history
        
        Returns:
            Complete prompt ready to send to LLM
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def parse_response(self, response: str) -> Dict:
        """
        Parse LLM response into structured action invocation.
        
        Args:
            response: Raw LLM response text
        
        Returns:
            Dictionary with 'tool' and 'args' keys
        """
        raise NotImplementedError("Subclasses must implement this method")


class AgentFunctionCallingLanguage(AgentLanguage):
    """
    Agent language using native LLM function calling.
    
    This uses the LLM's built-in function calling capability
    instead of custom parsing.
    """
    
    def format_goals(self, goals: List[Goal]) -> List[Dict]:
        """
        Format goals as system messages.
        
        Args:
            goals: List of agent goals
        
        Returns:
            List of message dictionaries
        """
        # Sort by priority (higher first)
        sorted_goals = sorted(goals, key=lambda g: g.priority, reverse=True)
        
        sep = "\n" + "=" * 50 + "\n"
        goal_text = "\n\n".join([
            f"GOAL: {goal.name}{sep}{goal.description}{sep}"
            for goal in sorted_goals
        ])
        
        return [{"role": "system", "content": goal_text}]
    
    def format_memory(self, memory: Memory) -> List[Dict]:
        """
        Format memory as conversation messages.
        
        Args:
            memory: Agent memory
        
        Returns:
            List of message dictionaries for the LLM
        """
        items = memory.get_memories()
        mapped_items = []
        
        for item in items:
            content = item.get("content")
            if content is None:
                content = json.dumps(item, indent=2)
            
            item_type = item.get("type", "user")
            
            # Map types to roles
            if item_type == "assistant":
                mapped_items.append({"role": "assistant", "content": content})
            elif item_type == "environment":
                # Environment results go as user messages
                mapped_items.append({"role": "user", "content": content})
            else:  # user, system, or other
                mapped_items.append({"role": "user", "content": content})
        
        return mapped_items
    
    def format_actions(self, actions: List[Action]) -> List[Dict]:
        """
        Format actions as function calling tools.
        
        Args:
            actions: Available actions
        
        Returns:
            List of tool definitions for the LLM
        """
        tools = []
        for action in actions:
            tools.append({
                "type": "function",
                "function": {
                    "name": action.name,
                    "description": action.description[:1024],  # Limit description length
                    "parameters": action.parameters,
                },
            })
        return tools
    
    def construct_prompt(
        self,
        actions: List[Action],
        environment: Environment,
        goals: List[Goal],
        memory: Memory
    ) -> Prompt:
        """
        Construct prompt using function calling format.
        
        Args:
            actions: Available actions
            environment: The environment
            goals: Agent goals
            memory: Conversation history
        
        Returns:
            Complete prompt with tools
        """
        messages = []
        messages.extend(self.format_goals(goals))
        messages.extend(self.format_memory(memory))
        
        tools = self.format_actions(actions)
        
        return Prompt(messages=messages, tools=tools)
    
    def parse_response(self, response: str) -> Dict:
        """
        Parse function calling response.
        
        Args:
            response: JSON string with tool and args
        
        Returns:
            Parsed dictionary with 'tool' and 'args'
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback: treat as terminate message
            return {
                "tool": "terminate",
                "args": {"message": response}
            }


# ============================================================================
# LLM INTERACTION
# ============================================================================

def generate_response(prompt: Prompt, model: str = DEFAULT_MODEL) -> str:
    """
    Generate a response from the LLM.
    
    Handles both regular completions and function calling.
    
    Args:
        prompt: The prompt to send
        model: Model identifier
    
    Returns:
        Response string (JSON for function calls, text otherwise)
    """
    messages = prompt.messages
    tools = prompt.tools
    
    if not tools:
        # Regular text completion
        response = completion(
            model=model,
            messages=messages,
            max_tokens=1024
        )
        return response.choices[0].message.content
    
    # Function calling completion
    response = completion(
        model=model,
        messages=messages,
        tools=tools,
        max_tokens=1024
    )
    
    # Check if LLM wants to call a function
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        result = {
            "tool": tool_call.function.name,
            "args": json.loads(tool_call.function.arguments),
        }
        return json.dumps(result)
    
    # No function call - return text
    return response.choices[0].message.content


# ============================================================================
# AGENT
# ============================================================================

class Agent:
    """
    The main Agent class implementing the GAME architecture.
    
    GAME stands for:
    - Goals: What to accomplish
    - Actions: What can be done
    - Memory: What is remembered
    - Environment: Where to operate
    """
    
    def __init__(
        self,
        goals: List[Goal],
        agent_language: AgentLanguage,
        action_registry: ActionRegistry,
        generate_response_fn: Callable[[Prompt], str],
        environment: Environment,
        verbose: bool = False
    ):
        """
        Initialize an agent.
        
        Args:
            goals: List of agent goals
            agent_language: Communication protocol
            action_registry: Available actions
            generate_response_fn: Function to call LLM
            environment: Operating environment
            verbose: Whether to print detailed logs
        """
        self.goals = goals
        self.agent_language = agent_language
        self.actions = action_registry
        self.generate_response = generate_response_fn
        self.environment = environment
        self.verbose = verbose
    
    def construct_prompt(
        self,
        goals: List[Goal],
        memory: Memory,
        actions: ActionRegistry
    ) -> Prompt:
        """
        Build a prompt with current state.
        
        Args:
            goals: Agent goals
            memory: Current memory
            actions: Available actions
        
        Returns:
            Complete prompt
        """
        return self.agent_language.construct_prompt(
            actions=actions.get_actions(),
            environment=self.environment,
            goals=goals,
            memory=memory
        )
    
    def get_action(self, response: str) -> tuple[Optional[Action], Dict]:
        """
        Parse response and retrieve the corresponding action.
        
        Args:
            response: LLM response string
        
        Returns:
            Tuple of (Action object, invocation dictionary)
        """
        invocation = self.agent_language.parse_response(response)
        action = self.actions.get_action(invocation["tool"])
        return action, invocation
    
    def should_terminate(self, response: str) -> bool:
        """
        Check if the agent should stop.
        
        Args:
            response: LLM response
        
        Returns:
            True if agent should terminate
        """
        action, _ = self.get_action(response)
        return action is not None and action.terminal
    
    def set_current_task(self, memory: Memory, task: str) -> None:
        """
        Initialize memory with user task.
        
        Args:
            memory: Memory object
            task: User's task description
        """
        memory.add_memory({"type": "user", "content": task})
    
    def update_memory(self, memory: Memory, response: str, result: Dict) -> None:
        """
        Update memory with agent decision and environment response.
        
        Args:
            memory: Memory object
            response: Agent's response
            result: Execution result
        """
        memory.add_memory({"type": "assistant", "content": response})
        memory.add_memory({"type": "environment", "content": json.dumps(result)})
    
    def run(
        self,
        user_input: str,
        memory: Optional[Memory] = None,
        max_iterations: int = DEFAULT_MAX_ITERATIONS
    ) -> Memory:
        """
        Execute the agent loop (GAME cycle).
        
        Args:
            user_input: User's task
            memory: Existing memory (or creates new)
            max_iterations: Maximum loop iterations
        
        Returns:
            Final memory state
        """
        memory = memory or Memory()
        self.set_current_task(memory, user_input)
        
        print("\n" + "=" * 70)
        print("🤖 AGENT FRAMEWORK (GAME Architecture)")
        print("=" * 70)
        print(f"📋 Task: {user_input}")
        print(f"🎯 Goals: {len(self.goals)}")
        print(f"🔧 Actions: {len(self.actions.get_actions())}")
        print(f"🔄 Max iterations: {max_iterations}\n")
        
        for iteration in range(max_iterations):
            print(f"{'─' * 70}")
            print(f"Iteration {iteration + 1}/{max_iterations}")
            print(f"{'─' * 70}")
            
            # Construct prompt
            prompt = self.construct_prompt(self.goals, memory, self.actions)
            
            # Generate response
            print("🧠 Agent thinking...")
            try:
                response = self.generate_response(prompt)
            except Exception as e:
                print(f"❌ Error generating response: {e}")
                break
            
            if self.verbose:
                print(f"📝 Full response:\n{response}\n")
            
            # Parse action
            action, invocation = self.get_action(response)
            
            if action is None:
                print(f"❌ Unknown action: {invocation.get('tool', 'unknown')}")
                break
            
            print(f"🔧 Action: {action.name}")
            if invocation.get("args"):
                print(f"   Args: {invocation['args']}")
            
            # Execute action
            result = self.environment.execute_action(action, invocation["args"])
            
            # Display result
            if result.get("tool_executed"):
                print(f"✅ Result: {result.get('result', 'Success')}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                if self.verbose and "traceback" in result:
                    print(f"Traceback:\n{result['traceback']}")
            
            # Update memory
            self.update_memory(memory, response, result)
            
            # Check termination
            if self.should_terminate(response):
                print("\n" + "=" * 70)
                print("✅ AGENT COMPLETED TASK")
                print("=" * 70)
                break
        
        return memory


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def create_file_agent() -> Agent:
    """
    Create an agent that can read files and generate documentation.
    
    Returns:
        Configured Agent instance
    """
    # Define goals
    goals = [
        Goal(
            priority=1,
            name="Read Project Files",
            description="Read each Python file in the project to understand its contents."
        ),
        Goal(
            priority=2,
            name="Generate Documentation",
            description="After reading all files, provide comprehensive documentation "
                       "in the terminate message."
        )
    ]
    
    # Define actions
    def list_project_files() -> List[str]:
        """List all Python files in current directory."""
        return sorted([f for f in os.listdir(".") if f.endswith(".py")])
    
    def read_project_file(name: str) -> str:
        """Read a project file."""
        try:
            with open(name, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading {name}: {str(e)}"
    
    def terminate_agent(message: str) -> str:
        """Terminate with summary."""
        return f"SUMMARY:\n{message}"
    
    # Create action registry
    action_registry = ActionRegistry()
    
    action_registry.register(Action(
        name="list_project_files",
        function=list_project_files,
        description="Lists all Python (.py) files in the current directory.",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        },
        terminal=False
    ))
    
    action_registry.register(Action(
        name="read_project_file",
        function=read_project_file,
        description="Reads the contents of a specified Python file.",
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The filename to read (e.g., 'main.py')"
                }
            },
            "required": ["name"]
        },
        terminal=False
    ))
    
    action_registry.register(Action(
        name="terminate",
        function=terminate_agent,
        description="Terminates the agent loop. Use this when the task is complete. "
                   "Provide a comprehensive summary of findings in the message.",
        parameters={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Summary of what was accomplished"
                }
            },
            "required": ["message"]
        },
        terminal=True
    ))
    
    # Create components
    agent_language = AgentFunctionCallingLanguage()
    environment = Environment()
    
    # Create agent
    return Agent(
        goals=goals,
        agent_language=agent_language,
        action_registry=action_registry,
        generate_response_fn=generate_response,
        environment=environment
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Advanced Agent Framework with GAME architecture"
    )
    parser.add_argument(
        '--task',
        type=str,
        default="Analyze the Python files in this project and create a README.",
        help='Task for the agent'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help='Maximum iterations'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    
    args = parser.parse_args()
    
    # Validate API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No API key found in environment variables")
        return 1
    
    try:
        # Create and run agent
        agent = create_file_agent()
        agent.verbose = args.verbose
        
        final_memory = agent.run(
            user_input=args.task,
            max_iterations=args.max_iterations
        )
        
        print("\n📊 Final Statistics:")
        print(f"   Total memory items: {len(final_memory)}")
        print(f"   Conversation turns: {len([m for m in final_memory.items if m.get('type') == 'assistant'])}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
