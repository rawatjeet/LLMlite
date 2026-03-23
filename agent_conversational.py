"""
Conversational Agent with Persistent Memory

A multi-turn chat agent that:
- Maintains a conversation loop (REPL-style) so you can keep talking
- Persists conversation history to disk as JSON so you can resume later
- Can use tools when needed, or just chat naturally
- Supports session management (create, resume, list sessions)

This fills the gap between "one-shot task agents" and real assistant UIs.

Usage:
    python agent_conversational.py                   # Start a new session
    python agent_conversational.py --resume latest   # Resume last session
    python agent_conversational.py --list-sessions   # Show saved sessions
    python agent_conversational.py --verbose
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
import sys
import argparse
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from litellm import completion

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))
SESSION_DIR = Path(os.getenv("SESSION_DIR", ".agent_sessions"))


# ---------------------------------------------------------------------------
# Session persistence
# ---------------------------------------------------------------------------

class Session:
    """Manages a conversation session with disk persistence."""

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or self._generate_id()
        self.messages: List[Dict] = []
        self.metadata: Dict[str, Any] = {
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": DEFAULT_MODEL,
            "turns": 0,
        }
        self._path = SESSION_DIR / f"{self.session_id}.json"

    @staticmethod
    def _generate_id() -> str:
        ts = time.strftime("%Y%m%d_%H%M%S")
        short = uuid.uuid4().hex[:6]
        return f"{ts}_{short}"

    def save(self) -> None:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "session_id": self.session_id,
            "metadata": self.metadata,
            "messages": self.messages,
        }
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, session_id: str) -> "Session":
        path = SESSION_DIR / f"{session_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Session '{session_id}' not found.")
        data = json.loads(path.read_text(encoding="utf-8"))
        session = cls(session_id=data["session_id"])
        session.messages = data["messages"]
        session.metadata = data["metadata"]
        return session

    @classmethod
    def load_latest(cls) -> "Session":
        if not SESSION_DIR.exists():
            raise FileNotFoundError("No sessions directory found.")
        files = sorted(SESSION_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            raise FileNotFoundError("No saved sessions found.")
        return cls.load(files[0].stem)

    @staticmethod
    def list_sessions() -> List[Dict]:
        if not SESSION_DIR.exists():
            return []
        sessions = []
        for f in sorted(SESSION_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                meta = data.get("metadata", {})
                first_user_msg = next(
                    (m["content"][:80] for m in data.get("messages", []) if m.get("role") == "user"),
                    "(no user message)",
                )
                sessions.append({
                    "id": f.stem,
                    "created": meta.get("created", "unknown"),
                    "turns": meta.get("turns", 0),
                    "preview": first_user_msg,
                })
            except Exception:
                continue
        return sessions

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
        self.metadata["turns"] += 1

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})


# ---------------------------------------------------------------------------
# Tools (available within conversation)
# ---------------------------------------------------------------------------

def list_files(directory: str = ".") -> str:
    try:
        items = sorted(i.name for i in Path(directory).iterdir())
        return "\n".join(items) if items else "(empty)"
    except Exception as e:
        return f"Error: {e}"


def read_file(file_name: str) -> str:
    try:
        p = Path(file_name)
        if not p.is_file():
            return f"Error: '{file_name}' not found or is not a file."
        return p.read_text(encoding="utf-8")[:20_000]
    except Exception as e:
        return f"Error: {e}"


def write_file(file_name: str, content: str) -> str:
    try:
        Path(file_name).write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to '{file_name}'."
    except Exception as e:
        return f"Error: {e}"


TOOL_FUNCTIONS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
}

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {"directory": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read text content of a file.",
            "parameters": {
                "type": "object",
                "properties": {"file_name": {"type": "string"}},
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["file_name", "content"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a helpful AI assistant with access to file system tools.

You can have natural multi-turn conversations. When the user asks about files,
code, or needs file operations, use the provided tools. Otherwise, just respond
conversationally.

Be concise but thorough. Remember context from earlier in the conversation.
"""


# ---------------------------------------------------------------------------
# Conversation loop
# ---------------------------------------------------------------------------

def chat_turn(session: Session, model: str, verbose: bool = False, max_tool_rounds: int = 5) -> str:
    """
    Process one user turn: call the LLM (possibly multiple times if it
    wants to use tools) and return the final text response.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + session.messages

    for _ in range(max_tool_rounds):
        resp = completion(model=model, messages=messages, tools=TOOLS_SPEC, max_tokens=DEFAULT_MAX_TOKENS)
        msg = resp.choices[0].message

        if not msg.tool_calls:
            text = msg.content or "(no response)"
            return text.strip()

        tool_call = msg.tool_calls[0]
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)

        if verbose:
            print(f"  [Tool: {fn_name}({fn_args})]")

        if fn_name in TOOL_FUNCTIONS:
            try:
                result = TOOL_FUNCTIONS[fn_name](**fn_args)
            except Exception as e:
                result = f"Error: {e}"
        else:
            result = f"Unknown tool: {fn_name}"

        if verbose:
            display = result[:300] + "..." if len(result) > 300 else result
            print(f"  [Result: {display}]")

        # Feed tool result back and continue
        action = json.dumps({"tool": fn_name, "args": fn_args})
        messages.append({"role": "assistant", "content": action})
        messages.append({"role": "user", "content": f"Tool result for {fn_name}:\n{result}"})

    return "I tried several tool calls but couldn't complete the request. Please try rephrasing."


def run_conversation(
    session: Session,
    model: str = DEFAULT_MODEL,
    verbose: bool = False,
) -> None:
    """Run the interactive conversation REPL."""
    print("\n" + "=" * 70)
    print("  CONVERSATIONAL AGENT")
    print("=" * 70)
    print(f"Session : {session.session_id}")
    print(f"Model   : {model}")
    print(f"History : {len(session.messages)} messages")
    print(f"\nType 'exit' or 'quit' to end. Type '/save' to save mid-conversation.")
    print(f"Type '/history' to see conversation history.")
    print("=" * 70 + "\n")

    if session.messages:
        recent = [m for m in session.messages if m["role"] in ("user", "assistant")][-4:]
        if recent:
            print("--- Recent conversation ---")
            for m in recent:
                role = "You" if m["role"] == "user" else "Agent"
                content = m["content"][:200]
                print(f"  {role}: {content}")
            print("---\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nEnding conversation.")
            break

        if not user_input:
            continue

        lower = user_input.lower()
        if lower in ("exit", "quit", "/exit", "/quit"):
            break
        if lower == "/save":
            session.save()
            print(f"  [Session saved: {session.session_id}]")
            continue
        if lower == "/history":
            for m in session.messages:
                role = m["role"].upper()
                print(f"  [{role}] {m['content'][:120]}")
            print()
            continue

        session.add_user_message(user_input)

        print("Agent: ", end="", flush=True)
        try:
            response = chat_turn(session, model, verbose)
        except Exception as e:
            response = f"Sorry, I encountered an error: {e}"

        print(response)
        print()

        session.add_assistant_message(response)
        session.save()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Conversational Agent with Persistent Memory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_conversational.py                    # New session
  python agent_conversational.py --resume latest    # Resume last session
  python agent_conversational.py --resume 20260322_143000_abc123
  python agent_conversational.py --list-sessions
  python agent_conversational.py --verbose

In-chat commands:
  /save     - Save session to disk
  /history  - Show conversation history
  exit      - End conversation (auto-saves)
""",
    )
    parser.add_argument("--resume", type=str, help="Session ID to resume ('latest' for most recent)")
    parser.add_argument("--list-sessions", action="store_true", help="List all saved sessions")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key found. Set GEMINI_API_KEY or OPENAI_API_KEY in .env")
        return 1

    if args.list_sessions:
        sessions = Session.list_sessions()
        if not sessions:
            print("No saved sessions.")
        else:
            print(f"\nSaved sessions ({len(sessions)}):\n")
            for s in sessions:
                print(f"  {s['id']}")
                print(f"    Created: {s['created']}  |  Turns: {s['turns']}")
                print(f"    Preview: {s['preview']}")
                print()
        return 0

    try:
        if args.resume:
            if args.resume.lower() == "latest":
                session = Session.load_latest()
            else:
                session = Session.load(args.resume)
            print(f"Resumed session: {session.session_id}")
        else:
            session = Session()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    try:
        run_conversation(session, model=args.model, verbose=args.verbose)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        session.save()
        print(f"\nSession saved: {session.session_id}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
