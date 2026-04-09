"""
Resume Builder Agent (Conversational + Plan-and-Execute Hybrid)

A multi-turn conversational agent that helps users build, optimize, and tailor
professional resumes. Combines two agent patterns:

  1. Conversational REPL — interactive Q&A to gather user info and preferences
  2. Plan-and-Execute — structured resume generation with section-by-section planning

The agent can:
  - Collect work experience, skills, education through natural conversation
  - Read an existing resume file and improve it
  - Tailor a resume to a specific job description
  - Score a resume against a job posting (ATS keyword analysis)
  - Output polished resumes in Markdown format

Usage:
    python agent_resume_builder.py
    python agent_resume_builder.py --task "Build a software engineer resume"
    python agent_resume_builder.py --task "Tailor my resume for this job" --resume-file my_resume.md
    python agent_resume_builder.py --resume-session latest
    python agent_resume_builder.py --list-sessions
    python agent_resume_builder.py --verbose
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
import re
import argparse
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from litellm import completion

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))
SESSION_DIR = Path(os.getenv("RESUME_SESSION_DIR", ".resume_sessions"))
OUTPUT_DIR = Path(os.getenv("RESUME_OUTPUT_DIR", "resumes_output"))


# ---------------------------------------------------------------------------
# Session persistence (resume-building sessions)
# ---------------------------------------------------------------------------

class ResumeSession:
    """Tracks a resume-building conversation with user profile data."""

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or self._generate_id()
        self.messages: List[Dict] = []
        self.profile: Dict[str, Any] = {
            "name": "",
            "contact": {},
            "summary": "",
            "experience": [],
            "education": [],
            "skills": [],
            "certifications": [],
            "projects": [],
        }
        self.metadata: Dict[str, Any] = {
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": DEFAULT_MODEL,
            "turns": 0,
            "resume_versions": 0,
        }
        self._path = SESSION_DIR / f"{self.session_id}.json"

    @staticmethod
    def _generate_id() -> str:
        ts = time.strftime("%Y%m%d_%H%M%S")
        short = uuid.uuid4().hex[:6]
        return f"resume_{ts}_{short}"

    def save(self) -> None:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "session_id": self.session_id,
            "metadata": self.metadata,
            "profile": self.profile,
            "messages": self.messages,
        }
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, session_id: str) -> "ResumeSession":
        path = SESSION_DIR / f"{session_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Resume session '{session_id}' not found.")
        data = json.loads(path.read_text(encoding="utf-8"))
        session = cls(session_id=data["session_id"])
        session.messages = data["messages"]
        session.metadata = data["metadata"]
        session.profile = data.get("profile", session.profile)
        return session

    @classmethod
    def load_latest(cls) -> "ResumeSession":
        if not SESSION_DIR.exists():
            raise FileNotFoundError("No resume sessions directory found.")
        files = sorted(SESSION_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            raise FileNotFoundError("No saved resume sessions found.")
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
                profile = data.get("profile", {})
                sessions.append({
                    "id": f.stem,
                    "created": meta.get("created", "unknown"),
                    "turns": meta.get("turns", 0),
                    "versions": meta.get("resume_versions", 0),
                    "name": profile.get("name", "(unnamed)"),
                })
            except Exception:
                continue
        return sessions


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def read_file(file_name: str) -> str:
    """Read a file (resume, job description, etc.)."""
    try:
        p = Path(file_name)
        if not p.is_file():
            return f"Error: '{file_name}' is not a file or does not exist."
        if p.stat().st_size > 100_000:
            return f"Error: File too large (>{100_000} bytes)."
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error: {e}"


def write_resume(file_name: str, content: str) -> str:
    """Write resume content to a Markdown file."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / file_name if not Path(file_name).is_absolute() else Path(file_name)
        out_path.write_text(content, encoding="utf-8")
        return f"Resume written to '{out_path}' ({len(content)} chars)."
    except Exception as e:
        return f"Error writing resume: {e}"


def save_profile(profile_json: str) -> str:
    """Save structured profile data extracted from conversation."""
    try:
        data = json.loads(profile_json)
        if not isinstance(data, dict):
            return "Error: profile_json must be a JSON object."
        return f"Profile updated with keys: {', '.join(data.keys())}"
    except json.JSONDecodeError as e:
        return f"Error parsing profile JSON: {e}"


def score_resume(resume_text: str, job_description: str) -> str:
    """Score a resume against a job description using keyword matching (ATS simulation)."""
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    jd_words = set(re.findall(r'\b[a-z]{3,}\b', jd_lower))
    resume_words = set(re.findall(r'\b[a-z]{3,}\b', resume_lower))

    stop_words = {
        "the", "and", "for", "are", "but", "not", "you", "all", "can",
        "had", "her", "was", "one", "our", "out", "has", "have", "been",
        "will", "with", "this", "that", "from", "they", "were", "which",
        "their", "about", "would", "there", "should", "could",
    }
    jd_keywords = jd_words - stop_words
    matched = jd_keywords & resume_words
    missing = jd_keywords - resume_words

    score = round(len(matched) / max(len(jd_keywords), 1) * 100, 1)

    top_missing = sorted(missing)[:20]
    top_matched = sorted(matched)[:20]

    return json.dumps({
        "ats_score": score,
        "keywords_in_jd": len(jd_keywords),
        "keywords_matched": len(matched),
        "keywords_missing": len(missing),
        "top_matched": top_matched,
        "top_missing_keywords": top_missing,
        "recommendation": (
            "Excellent match!" if score >= 75
            else "Good match, consider adding missing keywords." if score >= 50
            else "Needs improvement — many key terms are missing."
        ),
    }, indent=2)


def list_resume_files(directory: str = ".") -> str:
    """List resume-related files in a directory."""
    try:
        p = Path(directory)
        extensions = {".md", ".txt", ".pdf", ".docx", ".doc"}
        items = sorted(
            item.name for item in p.iterdir()
            if item.is_file() and item.suffix.lower() in extensions
        )
        return "\n".join(items) if items else "(no resume files found)"
    except Exception as e:
        return f"Error: {e}"


TOOL_FUNCTIONS: Dict[str, Callable] = {
    "read_file": read_file,
    "write_resume": write_resume,
    "save_profile": save_profile,
    "score_resume": score_resume,
    "list_resume_files": list_resume_files,
}

TOOLS_SPEC: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file (existing resume, job description, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "Path to the file to read"}
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_resume",
            "description": "Write the generated resume to a Markdown file in the output directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "Output file name (e.g. 'john_doe_resume.md')",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full resume content in Markdown format",
                    },
                },
                "required": ["file_name", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_profile",
            "description": (
                "Save structured profile data extracted from conversation. "
                "Pass a JSON object with keys like 'name', 'experience', 'skills', etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "profile_json": {
                        "type": "string",
                        "description": "JSON string of profile data to merge",
                    }
                },
                "required": ["profile_json"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "score_resume",
            "description": (
                "Score a resume against a job description using ATS-style keyword analysis. "
                "Returns match percentage and missing keywords."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_text": {"type": "string", "description": "Full resume text"},
                    "job_description": {"type": "string", "description": "Job description text"},
                },
                "required": ["resume_text", "job_description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_resume_files",
            "description": "List resume-related files (.md, .txt, .pdf, .docx) in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to search (default '.')"}
                },
                "required": [],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert Resume Builder assistant. You help users create, \
improve, and tailor professional resumes.

## Your Capabilities
- Build resumes from scratch through conversation
- Read and improve existing resumes
- Tailor resumes to specific job descriptions
- Score resumes against job postings (ATS keyword analysis)
- Write polished resumes in Markdown format

## Resume Best Practices You Follow
- Use strong action verbs (Led, Designed, Implemented, Optimized, etc.)
- Quantify achievements with numbers and percentages where possible
- Keep bullet points concise (1-2 lines each)
- Tailor content to the target role / industry
- Use reverse chronological order for experience and education
- Include a compelling professional summary (2-3 sentences)
- Highlight relevant skills matching the job description
- Ensure ATS-friendly formatting (clean sections, standard headings)

## Conversation Flow
1. If no existing resume is provided, gather information section by section:
   - Name and contact info
   - Professional summary / objective
   - Work experience (company, role, dates, achievements)
   - Education
   - Skills (technical + soft)
   - Certifications, projects, or other relevant sections
2. After gathering info, generate the resume and write it to a file.
3. Offer to score it against a job description if the user has one.
4. Iterate on feedback — the user can ask for revisions.

## Output Format
When writing a resume, use clean Markdown with these sections:
- # Name
- Contact line (email | phone | location | LinkedIn)
- ## Professional Summary
- ## Experience (with ### for each role)
- ## Education
- ## Skills
- Additional sections as needed

Use the save_profile tool to persist structured data as you collect it.
Use write_resume to save the final resume file.
Use score_resume when comparing against a job description.

{profile_context}
"""


# ---------------------------------------------------------------------------
# Conversation engine
# ---------------------------------------------------------------------------

def build_system_prompt(session: ResumeSession) -> str:
    """Build system prompt with current profile context."""
    profile = session.profile
    parts = []
    if profile.get("name"):
        parts.append(f"User's name: {profile['name']}")
    if profile.get("experience"):
        parts.append(f"Experience entries collected: {len(profile['experience'])}")
    if profile.get("skills"):
        parts.append(f"Skills: {', '.join(profile['skills'][:10])}")
    if profile.get("education"):
        parts.append(f"Education entries: {len(profile['education'])}")

    context = ""
    if parts:
        context = "\n## Current Profile Data\n" + "\n".join(f"- {p}" for p in parts)

    return SYSTEM_PROMPT.format(profile_context=context)


def chat_turn(
    session: ResumeSession,
    model: str,
    verbose: bool = False,
    max_tool_rounds: int = 8,
) -> str:
    """Process one user turn, handling tool calls, and return the final text."""
    system_prompt = build_system_prompt(session)
    messages = [{"role": "system", "content": system_prompt}] + session.messages

    for round_num in range(max_tool_rounds):
        resp = completion(
            model=model,
            messages=messages,
            tools=TOOLS_SPEC,
            max_tokens=DEFAULT_MAX_TOKENS,
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            text = msg.content or "(no response)"
            return text.strip()

        tool_call = msg.tool_calls[0]
        fn_name = tool_call.function.name
        fn_args = json.loads(tool_call.function.arguments)

        if verbose:
            print(f"\n  [Tool #{round_num + 1}: {fn_name}({json.dumps(fn_args)[:200]})]")

        if fn_name == "save_profile":
            try:
                updates = json.loads(fn_args.get("profile_json", "{}"))
                for key, value in updates.items():
                    if key in session.profile:
                        if isinstance(session.profile[key], list) and isinstance(value, list):
                            session.profile[key].extend(value)
                        else:
                            session.profile[key] = value
                result = f"Profile updated: {', '.join(updates.keys())}"
                session.save()
            except Exception as e:
                result = f"Error updating profile: {e}"
        elif fn_name == "write_resume":
            result = TOOL_FUNCTIONS[fn_name](**fn_args)
            session.metadata["resume_versions"] += 1
            session.save()
        elif fn_name in TOOL_FUNCTIONS:
            try:
                result = TOOL_FUNCTIONS[fn_name](**fn_args)
            except Exception as e:
                result = f"Error: {e}"
        else:
            result = f"Unknown tool: {fn_name}"

        if verbose:
            display = result[:400] + "..." if len(result) > 400 else result
            print(f"  [Result: {display}]")

        action = json.dumps({"tool": fn_name, "args": fn_args})
        messages.append({"role": "assistant", "content": action})
        messages.append({"role": "user", "content": f"Tool result for {fn_name}:\n{result}"})

    return "I used several tools but couldn't finish. Could you rephrase or provide more detail?"


def run_conversation(
    session: ResumeSession,
    model: str = DEFAULT_MODEL,
    initial_task: Optional[str] = None,
    resume_file: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """Run the interactive resume-building REPL."""
    print("\n" + "=" * 70)
    print("  RESUME BUILDER AGENT")
    print("=" * 70)
    print(f"Session : {session.session_id}")
    print(f"Model   : {model}")
    print(f"History : {len(session.messages)} messages")
    print(f"Output  : {OUTPUT_DIR.resolve()}")
    print(f"\nCommands: 'exit' to quit | '/save' to save | '/score' to score resume")
    print(f"          '/profile' to view collected info | '/history' for chat log")
    print("=" * 70 + "\n")

    if resume_file:
        content = read_file(resume_file)
        if not content.startswith("Error"):
            bootstrap = f"Here is my existing resume from '{resume_file}':\n\n{content}"
            if initial_task:
                bootstrap += f"\n\nMy request: {initial_task}"
            else:
                bootstrap += "\n\nPlease review it and suggest improvements."
            session.add_user_message(bootstrap)
            print("Agent: ", end="", flush=True)
            try:
                response = chat_turn(session, model, verbose)
            except Exception as e:
                response = f"Sorry, I encountered an error: {e}"
            print(response + "\n")
            session.add_assistant_message(response)
            session.save()
        else:
            print(f"Warning: Could not read '{resume_file}': {content}\n")

    elif initial_task:
        session.add_user_message(initial_task)
        print("Agent: ", end="", flush=True)
        try:
            response = chat_turn(session, model, verbose)
        except Exception as e:
            response = f"Sorry, I encountered an error: {e}"
        print(response + "\n")
        session.add_assistant_message(response)
        session.save()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nEnding session.")
            break

        if not user_input:
            continue

        lower = user_input.lower()
        if lower in ("exit", "quit", "/exit", "/quit"):
            break
        if lower == "/save":
            session.save()
            print(f"  [Session saved: {session.session_id}]\n")
            continue
        if lower == "/profile":
            print("\n--- Collected Profile ---")
            for key, val in session.profile.items():
                if val:
                    display = json.dumps(val, indent=2) if isinstance(val, (list, dict)) else str(val)
                    print(f"  {key}: {display[:200]}")
            print("---\n")
            continue
        if lower == "/history":
            for m in session.messages:
                role = m["role"].upper()
                print(f"  [{role}] {m['content'][:120]}")
            print()
            continue
        if lower == "/score":
            print("  Paste the job description (end with a blank line):")
            jd_lines = []
            while True:
                try:
                    line = input()
                except (EOFError, KeyboardInterrupt):
                    break
                if not line:
                    break
                jd_lines.append(line)
            if jd_lines:
                jd = "\n".join(jd_lines)
                resume_files = list(OUTPUT_DIR.glob("*.md")) if OUTPUT_DIR.exists() else []
                if resume_files:
                    latest = max(resume_files, key=lambda p: p.stat().st_mtime)
                    resume_text = latest.read_text(encoding="utf-8")
                    result = score_resume(resume_text, jd)
                    print(f"\n  ATS Score for '{latest.name}':\n{result}\n")
                else:
                    print("  No resume files found. Generate a resume first.\n")
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


def add_user_message(session: ResumeSession, content: str) -> None:
    session.messages.append({"role": "user", "content": content})
    session.metadata["turns"] += 1


def add_assistant_message(session: ResumeSession, content: str) -> None:
    session.messages.append({"role": "assistant", "content": content})


ResumeSession.add_user_message = add_user_message
ResumeSession.add_assistant_message = add_assistant_message


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resume Builder Agent — build, improve, and tailor resumes with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_resume_builder.py
  python agent_resume_builder.py --task "Build a data scientist resume"
  python agent_resume_builder.py --task "Tailor for Google SWE role" --resume-file resume.md
  python agent_resume_builder.py --resume-session latest
  python agent_resume_builder.py --list-sessions
  python agent_resume_builder.py --verbose

In-session commands:
  /save      - Save session to disk
  /profile   - View collected profile data
  /score     - Score latest resume against a job description
  /history   - Show conversation history
  exit       - End session (auto-saves)

Pattern explained:
  This agent combines conversational REPL (for gathering info interactively)
  with structured tool use (for reading/writing files, scoring resumes).
  Profile data persists across sessions so you can iteratively refine.
""",
    )
    parser.add_argument("--task", type=str, help="Initial task or goal for the agent")
    parser.add_argument("--resume-file", type=str, help="Path to an existing resume file to improve")
    parser.add_argument("--resume-session", type=str, help="Resume session ID to continue ('latest' for most recent)")
    parser.add_argument("--list-sessions", action="store_true", help="List all saved resume sessions")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key found. Set GEMINI_API_KEY or OPENAI_API_KEY in .env")
        return 1

    if args.list_sessions:
        sessions = ResumeSession.list_sessions()
        if not sessions:
            print("No saved resume sessions.")
        else:
            print(f"\nResume sessions ({len(sessions)}):\n")
            for s in sessions:
                print(f"  {s['id']}")
                print(f"    Name: {s['name']}  |  Created: {s['created']}  |  Turns: {s['turns']}  |  Versions: {s['versions']}")
                print()
        return 0

    try:
        if args.resume_session:
            if args.resume_session.lower() == "latest":
                session = ResumeSession.load_latest()
            else:
                session = ResumeSession.load(args.resume_session)
            print(f"Resumed session: {session.session_id}")
        else:
            session = ResumeSession()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    try:
        run_conversation(
            session,
            model=args.model,
            initial_task=args.task,
            resume_file=args.resume_file,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        session.save()
        print(f"\nSession saved: {session.session_id}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
