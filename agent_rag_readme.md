# RAG Agent (Retrieval-Augmented Generation)

An agent that answers questions about a codebase or document collection by indexing files into chunks, finding the most relevant pieces, and generating grounded answers with source citations.

---

## Architecture

```
                    INDEXING PHASE
                    ==============
  Files on disk ──> [Chunk into segments] ──> [Build TF-IDF index]
  (.py, .md, .txt)    (40 lines each,           (vocabulary +
                        10-line overlap)          term frequencies)


                    QUERY PHASE
                    ===========
  User Question ──> [Tokenize query]
                        |
                        v
                    [TF-IDF search against all chunks]
                        |
                        v
                    [Top-K most relevant chunks]
                        |
                        v
                    [LLM generates answer with context]
                        |
                        v
                    Answer with source citations
```

## Why This Pattern Matters

LLMs have a fixed context window. You can't feed an entire codebase into a single prompt. RAG solves this by:
1. **Chunking** - Breaking files into manageable pieces
2. **Retrieving** - Finding only the relevant pieces
3. **Grounding** - The LLM answers based on actual data, not hallucination

This implementation uses TF-IDF (no external vector database needed), keeping it dependency-free and fast for local codebases.

---

## Key Features

- **Zero external dependencies**: Uses built-in TF-IDF instead of a vector database
- **Overlapping chunks**: 10-line overlap prevents losing context at chunk boundaries
- **Source citations**: Answers include file paths and line numbers
- **Interactive mode**: Ask multiple questions in a session
- **Configurable scope**: Choose which file extensions to index

## Components

### Indexing

| Function | Purpose |
|----------|---------|
| `chunk_file()` | Split a file into overlapping line-based segments |
| `index_directory()` | Walk directory tree, chunk all matching files |

### Retrieval

| Function | Purpose |
|----------|---------|
| `tokenize()` | Simple word tokenizer (lowercase, alphanumeric) |
| `build_idf()` | Compute inverse document frequency for all terms |
| `tfidf_score()` | Score a query against a single chunk |
| `retrieve()` | Find top-k highest-scoring chunks |

### Generation

| Function | Purpose |
|----------|---------|
| `generate_answer()` | Send question + retrieved chunks to LLM |

---

## Prerequisites

1. Python 3.8+
2. Dependencies installed: `pip install -r requirements.txt`
3. API key in `.env`:
   ```
   GEMINI_API_KEY=your-key-here
   ```

## Quick Start

```bash
# Interactive Q&A about current directory
python agent_rag.py

# Single question
python agent_rag.py --task "How does the agent loop work?"

# Search specific directory with more results
python agent_rag.py --directory ./src --top-k 8

# Only index Python files
python agent_rag.py --extensions .py

# See retrieval details
python agent_rag.py --task "What tools are defined?" --verbose
```

## Example Session

```
======================================================================
  RAG AGENT (Retrieval-Augmented Generation)
======================================================================
Directory : C:\gitProjects\LLMlite
Extensions: .py, .md, .txt
Model     : gemini/gemini-1.5-flash
Top-K     : 5

Phase 1: INDEXING
----------------------------------------
  Indexed 12 files -> 47 chunks

  Building search index...
  Vocabulary: 1,842 unique terms

Phase 2: ASK QUESTIONS
----------------------------------------
Ask questions about the codebase. Type 'exit' to quit.

Question: What agent patterns are implemented?

  Searching for relevant chunks...
  Found 5 relevant chunks:
    1. README.md (L45-85): ## Agent Implementations...
    2. agent_react.py (L1-40): """ReAct Agent (Reasoning + Acting)...
    3. agent_planner.py (L1-40): """Plan-and-Execute Agent...
    4. agent_multi.py (L1-40): """Multi-Agent Orchestrator...
    5. agent_critic.py (L1-40): """Generator-Critic Agent...

  Generating answer...

======================================================================
  ANSWER
======================================================================

Based on the codebase, the following agent patterns are implemented:

1. **ReAct** (`agent_react.py`, L1-18) - Reasoning + Acting pattern where the LLM
   produces Thought → Action → Observation sequences.

2. **Plan-then-Execute** (`agent_planner.py`, L1-15) - Two-phase agent that first
   generates a step-by-step plan, then executes each step.

[... more patterns listed with citations ...]
======================================================================
```

## How It Works

### Chunking Strategy

Files are split into fixed-size chunks with overlap:

```
File: 100 lines, chunk_size=40, overlap=10

Chunk 1: Lines 1-40
Chunk 2: Lines 31-70    (overlaps with Chunk 1 by 10 lines)
Chunk 3: Lines 61-100   (overlaps with Chunk 2 by 10 lines)
```

Overlap ensures that content near chunk boundaries isn't lost.

### TF-IDF Retrieval

For each query:
1. Tokenize the query into words
2. For each chunk, compute TF-IDF score: `sum(TF(term, chunk) * IDF(term))`
3. Sort chunks by score descending
4. Return top-k chunks

This is a classical information retrieval technique that works surprisingly well for keyword-heavy code searches.

### Grounded Generation

The retrieved chunks are injected into the prompt:

```
[Source 1: agent_react.py lines 1-40]
<chunk content>

[Source 2: README.md lines 45-85]
<chunk content>

Question: What agent patterns are implemented?
```

The system prompt instructs the LLM to cite sources and only use provided context.

## Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `--task` | (interactive) | Question to answer |
| `--directory` | `.` | Root directory to index |
| `--extensions` | `.py .md .txt` | File types to include |
| `--top-k` | 5 | Number of chunks to retrieve |
| `--model` | `gemini/gemini-1.5-flash` | LLM model |
| `--verbose` | off | Show retrieval details |

Environment variables:
- `DEFAULT_MODEL` - Override default model
- `DEFAULT_MAX_TOKENS` - Max tokens per LLM call (default: 2048)
- `GEMINI_API_KEY` or `OPENAI_API_KEY` - API authentication

### Tuning Tips

| Parameter | Too Low | Too High | Recommended |
|-----------|---------|----------|-------------|
| `chunk_size` | Loses context | Dilutes relevance | 30-50 lines |
| `overlap` | Misses boundaries | Redundant chunks | 25% of chunk_size |
| `top_k` | Misses info | Noise in context | 3-8 |

## When to Use This Agent

**Good for:**
- Answering questions about unfamiliar codebases
- Finding where specific functionality is implemented
- Documentation Q&A
- Code review support (find related code)

**Not ideal for:**
- Tasks that need to modify files (use ReAct or Plan-then-Execute)
- Semantic similarity search (TF-IDF is keyword-based)
- Real-time streaming data

## Cost Estimate

Per question (with top-5 retrieval):
- Input tokens: ~2,000-5,000 (depends on chunk size)
- Output tokens: ~300-800
- Estimated cost: $0.001-0.003 with Gemini Flash
- Indexing is free (local computation only)

---

## Comparison with Other Agents

| Feature | RAG | ReAct | Conversational |
|---------|-----|-------|---------------|
| Reads files | Indexes at start | On demand | On demand |
| Search method | TF-IDF scoring | LLM decides | User provides |
| Best for | Q&A over docs | General tasks | Interactive chat |
| Grounded | Yes (cited) | Partially | No |

## Possible Enhancements

- Replace TF-IDF with embedding-based similarity (requires `sentence-transformers`)
- Add a vector store like ChromaDB or FAISS for persistent indexing
- Implement query expansion: LLM rewrites the query for better retrieval
- Add re-ranking: Use a second LLM call to re-rank retrieved chunks
