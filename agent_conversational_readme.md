# Conversational Agent with Persistent Memory

A multi-turn chat agent that maintains natural conversations, uses tools when needed, and persists session history to disk so you can resume conversations later. This bridges the gap between one-shot task agents and real assistant interfaces.

## Files Covered

| File | Lines | Description |
|------|-------|-------------|
| **agent_conversational.py** | ~310 | Multi-turn REPL agent with `Session` class for disk persistence (JSON), tool calling within conversation flow, session management (create/resume/list), and in-chat commands. |

## 🎯 What Makes This Different?

| Agent | Interaction | Memory | Persistence |
|-------|------------|--------|-------------|
| agent_tools.py | Single task → done | In-memory only | ❌ Lost on exit |
| agent_react.py | Single task → done | In-memory only | ❌ Lost on exit |
| agent_planner.py | Single task → done | In-memory only | ❌ Lost on exit |
| **agent_conversational.py** | **Multi-turn chat** | **Full history** | **✅ Saved to disk** |

This is the only agent in the project that supports:
- **Multiple exchanges** in a single session
- **Resuming** a previous conversation
- **Natural chat** mixed with tool use

## 📊 Architecture

```bash
┌─────────────────────────────────────────────────────┐
│                   USER (REPL)                       │
│                                                     │
│  You: What Python files are here?                   │
│  Agent: Let me check... Found 12 Python files:      │
│         main.py, agent_tools.py, ...                │
│                                                     │
│  You: Read main.py and tell me what it does         │
│  Agent: main.py is a simple API test script that... │
│                                                     │
│  You: exit                                          │
│  Session saved: 20260322_143000_abc123              │
│                                                     │
├─────────────────────────────────────────────────────┤
│                  SESSION (Disk)                     │
│                                                     │
│  .agent_sessions/                                   │
│    └── 20260322_143000_abc123.json                  │
│        {                                            │
│          "session_id": "20260322_143000_abc123",    │
│          "metadata": {                              │
│            "created": "2026-03-22 14:30:00",        │
│            "turns": 4                               │
│          },                                         │
│          "messages": [                              │
│            {"role": "user", "content": "What..."},  │
│            {"role": "assistant", "content": "..."},  │
│            ...                                      │
│          ]                                          │
│        }                                            │
│                                                     │
├─────────────────────────────────────────────────────┤
│                  TOOLS (On-demand)                  │
│                                                     │
│  The agent can use tools transparently:             │
│  list_files → read_file → write_file               │
│  Tool calls happen behind the scenes when needed    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 🌟 Key Features

- **Natural Multi-Turn Chat**: Keep asking follow-up questions naturally
- **Persistent Sessions**: Conversations saved to `.agent_sessions/` as JSON
- **Resume Conversations**: Pick up where you left off with `--resume`
- **Session Management**: List, create, and resume sessions
- **Transparent Tool Use**: Agent uses tools when needed, chats normally otherwise
- **In-Chat Commands**: `/save`, `/history`, `exit`
- **Auto-Save**: Session saved after every exchange

## 🛠️ Available Tools

| Tool | Description | When Used |
|------|-------------|-----------|
| `list_files(directory)` | List files at a path | When user asks about files |
| `read_file(file_name)` | Read file content (max 20 KB) | When user asks to read a file |
| `write_file(file_name, content)` | Write text to a file | When user asks to create/write files |

The agent decides automatically whether to use tools or just respond conversationally.

## 📋 Prerequisites

- **Python 3.8+**
- **API Key**: Gemini (recommended) or OpenAI
- Install dependencies: `pip install -r requirements.txt`

## 🚀 Quick Start

### Installation

```bash
pip install litellm python-dotenv
echo "GEMINI_API_KEY=your-key-here" > .env
```

### Start a New Session

```bash
python agent_conversational.py
```

### Resume Last Session

```bash
python agent_conversational.py --resume latest
```

### Resume a Specific Session

```bash
python agent_conversational.py --resume 20260322_143000_abc123
```

### List All Sessions

```bash
python agent_conversational.py --list-sessions
```

## 📝 Example Session

```bash
$ python agent_conversational.py

======================================================================
  CONVERSATIONAL AGENT
======================================================================
Session : 20260322_153045_f2a1b3
Model   : gemini/gemini-1.5-flash
History : 0 messages

Type 'exit' or 'quit' to end. Type '/save' to save mid-conversation.
Type '/history' to see conversation history.
======================================================================

You: Hi! What files are in this project?

Agent: I found the following files in the current directory:

- main.py
- agent_tools.py
- agent_react.py
- agent_planner.py
- agent_conversational.py
- quasi-agent.py
- requirements.txt
- .env
... and 20 more files.

You: Can you read agent_react.py and tell me what pattern it implements?

Agent: agent_react.py implements the ReAct (Reasoning + Acting) pattern.
It forces the LLM to produce explicit Thought → Action → Observation
triples on every turn. The file includes 6 tools (list_files, read_file,
write_file, search_in_file, shell_command, finish) and uses regex-based
parsing to extract the Thought and Action from the LLM's response.

You: How is that different from agent_planner.py?

Agent: Great question! The key difference is:

- **ReAct** (agent_react.py): Reasons step-by-step, deciding what to do
  next after each observation. No upfront plan.
- **Plan-and-Execute** (agent_planner.py): Creates an explicit numbered
  plan first, then executes each step methodically.

ReAct is better for exploratory tasks; Plan-and-Execute is better when
you can predict the steps ahead of time.

You: /save
  [Session saved: 20260322_153045_f2a1b3]

You: exit

Session saved: 20260322_153045_f2a1b3
```

### Resuming Later

```bash
$ python agent_conversational.py --resume latest

======================================================================
  CONVERSATIONAL AGENT
======================================================================
Session : 20260322_153045_f2a1b3
Model   : gemini/gemini-1.5-flash
History : 6 messages

--- Recent conversation ---
  You: Can you read agent_react.py and tell me what pattern it implements?
  Agent: agent_react.py implements the ReAct (Reasoning + Acting) pattern...
  You: How is that different from agent_planner.py?
  Agent: Great question! The key difference is: ...
---

You: Can you create a comparison table in a file?

Agent: I've created a file called `agent_comparison.md` with a detailed
comparison table covering all agent patterns in this project.

You: Thanks! exit

Session saved: 20260322_153045_f2a1b3
```

## 🔧 In-Chat Commands

| Command | Action |
|---------|--------|
| `exit` or `quit` | End conversation (auto-saves) |
| `/save` | Save session to disk immediately |
| `/history` | Display full conversation history |

## 📂 Session Storage

Sessions are stored in `.agent_sessions/` as JSON files:

```
.agent_sessions/
├── 20260322_143000_abc123.json
├── 20260322_153045_f2a1b3.json
└── 20260323_091500_d4e5f6.json
```

### Session File Format

```json
{
  "session_id": "20260322_143000_abc123",
  "metadata": {
    "created": "2026-03-22 14:30:00",
    "model": "gemini/gemini-1.5-flash",
    "turns": 4
  },
  "messages": [
    {"role": "user", "content": "What files are here?"},
    {"role": "assistant", "content": "I found the following files..."},
    {"role": "user", "content": "Read main.py"},
    {"role": "assistant", "content": "main.py is a test script..."}
  ]
}
```

### Listing Sessions

```bash
$ python agent_conversational.py --list-sessions

Saved sessions (3):

  20260323_091500_d4e5f6
    Created: 2026-03-23 09:15:00  |  Turns: 2
    Preview: Tell me about the agent framework

  20260322_153045_f2a1b3
    Created: 2026-03-22 15:30:45  |  Turns: 4
    Preview: What files are in this project?

  20260322_143000_abc123
    Created: 2026-03-22 14:30:00  |  Turns: 8
    Preview: Help me understand the codebase
```

## ⚙️ Configuration

### Environment Variables

```env
GEMINI_API_KEY=your-key
OPENAI_API_KEY=your-key
DEFAULT_MODEL=gemini/gemini-1.5-flash
DEFAULT_MAX_TOKENS=2048
SESSION_DIR=.agent_sessions
```

### CLI Options

```bash
--resume SESSION_ID     # Resume a session ('latest' for most recent)
--list-sessions         # Show all saved sessions
--model MODEL_NAME      # LLM model to use
--verbose               # Show tool calls and results
```

## 🔍 Comparison with Other Agents

| Feature | Task Agents | **Conversational Agent** |
|---------|------------|------------------------|
| **Interaction** | One task → done | ✅ Multi-turn chat |
| **Follow-ups** | ❌ Start over | ✅ Natural follow-ups |
| **Session persistence** | ❌ Lost | ✅ Saved to disk |
| **Resume later** | ❌ No | ✅ `--resume latest` |
| **Tool use** | Always uses tools | Uses tools when needed |
| **Natural chat** | Task-focused only | ✅ Conversational + tools |

## 💰 Cost Considerations

Each conversation turn = 1 LLM call (+ 0-5 tool calls if tools are needed):

| Scenario | Calls per Turn | Cost (GPT-4) |
|----------|---------------|---------------|
| Simple chat | 1 | ~$0.03 |
| Chat + 1 tool | 2 | ~$0.06 |
| Chat + 3 tools | 4 | ~$0.12 |

**Tip**: Longer conversations accumulate history, increasing token usage. For very long sessions, consider starting a new session periodically.

## 🐛 Troubleshooting

### "Session not found"

**Cause**: Session ID doesn't exist in `.agent_sessions/`.
**Solution**: Use `--list-sessions` to see available sessions, or use `--resume latest`.

### Responses get slower over time

**Cause**: Full conversation history is sent with every request. Long sessions = more tokens.
**Solution**: Start a new session for unrelated topics. The agent remembers everything in the current session.

### Agent uses tools when it shouldn't (or vice versa)

**Cause**: The LLM decides autonomously when to use tools.
**Solution**: Be explicit in your requests. Say "read the file" vs "tell me about the file" to control tool usage.

### Session file is corrupted

**Solution**: Delete the corrupted JSON file from `.agent_sessions/` and start a new session.

## 📚 Learning Path

After mastering this agent:

1. **Add more tools**: Web search, code execution, database queries
2. **Implement summarization**: Compress old history to save tokens
3. **Add user profiles**: Remember preferences across sessions
4. **Build a web UI**: Wrap the conversation loop in a Flask/FastAPI server
5. **Add RAG**: Retrieve relevant documents to augment responses

## 📖 Further Reading

- [ChatGPT Architecture](https://openai.com/blog/chatgpt) - How conversational AI works
- [Memory in AI Agents](https://www.pinecone.io/learn/langchain-conversational-memory/) - Different memory strategies
- [LangChain Conversation Memory](https://python.langchain.com/docs/modules/memory/) - Framework memory types
- [LiteLLM Documentation](https://docs.litellm.ai/)
