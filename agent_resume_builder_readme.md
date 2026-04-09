# Resume Builder Agent

## Pattern: Conversational + Tool Use (Hybrid)

This agent combines a **conversational REPL** (like `agent_conversational.py`) with **structured tool use** for file I/O and resume scoring. It's designed for tasks where interactive back-and-forth is essential — building a resume requires asking questions, gathering context, and iterating.

## What It Does

| Capability | How |
|---|---|
| Build resume from scratch | Guided conversation to collect experience, skills, education |
| Improve existing resume | Reads a file, suggests improvements via LLM analysis |
| Tailor to a job description | Adjusts language, keywords, and emphasis to match a posting |
| ATS keyword scoring | Compares resume against job description, reports match % |
| Persistent sessions | Resume-building sessions save to disk and can be resumed |
| Profile data extraction | Structured profile JSON persists across sessions |

## Architecture

```
User Input
    │
    ▼
┌──────────────────────┐
│   Conversational      │◄── Session persistence (.resume_sessions/)
│   REPL Loop           │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│   LLM (litellm)      │──► Tool calls (function calling API)
│   + System Prompt     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│   Tools:              │
│   • read_file         │──► Read existing resumes / JDs
│   • write_resume      │──► Output to resumes_output/
│   • save_profile      │──► Persist structured data
│   • score_resume      │──► ATS keyword analysis
│   • list_resume_files │──► Find existing files
└──────────────────────┘
```

## Tools

| Tool | Purpose |
|---|---|
| `read_file` | Read an existing resume or job description from disk |
| `write_resume` | Write the generated resume as Markdown to `resumes_output/` |
| `save_profile` | Persist structured profile data (name, experience, skills, etc.) |
| `score_resume` | ATS-style keyword matching: resume vs. job description |
| `list_resume_files` | List `.md`, `.txt`, `.pdf`, `.docx` files in a directory |

## Usage Examples

```bash
# Start fresh — the agent will guide you through building a resume
python agent_resume_builder.py

# Give it a specific goal
python agent_resume_builder.py --task "Build a data scientist resume for FAANG companies"

# Improve an existing resume
python agent_resume_builder.py --resume-file my_resume.md

# Tailor for a specific role
python agent_resume_builder.py --task "Tailor for this Google SWE posting" --resume-file resume.md

# Resume a previous session
python agent_resume_builder.py --resume-session latest
python agent_resume_builder.py --list-sessions

# Verbose mode (shows tool calls)
python agent_resume_builder.py --verbose
```

## In-Session Commands

| Command | Action |
|---|---|
| `/save` | Save session to disk |
| `/profile` | View all collected profile data |
| `/score` | Score latest resume against a pasted job description |
| `/history` | Show conversation history |
| `exit` | End session (auto-saves) |

## Key Learning Points

1. **Conversational + tools hybrid**: Unlike one-shot task agents, this maintains a REPL but can use tools when needed — the model decides when to chat vs. when to call a tool.

2. **Profile accumulation**: The `save_profile` tool lets the LLM extract structured data from free-text conversation and persist it. This is a common pattern in form-filling agents.

3. **Dynamic system prompts**: The system prompt is rebuilt each turn with current profile data, giving the LLM context without re-reading the full conversation.

4. **ATS scoring without AI**: The `score_resume` tool uses deterministic keyword matching (no LLM call), demonstrating that not every tool needs to be AI-powered.

## Output

Resumes are saved as Markdown files in `resumes_output/`. The Markdown format is:
- ATS-friendly (parseable by automated systems)
- Human-readable
- Easily convertible to PDF (use `md_to_pdf.py` or any Markdown-to-PDF tool)

## Extending This Agent

- **PDF export**: Pipe the Markdown output through `md_to_pdf.py` or add `fpdf2`
- **LinkedIn import**: Add a tool that fetches LinkedIn profile data via API
- **Multiple formats**: Add tools for different resume formats (functional, combination)
- **Industry templates**: Pre-load industry-specific templates as system prompt variants
