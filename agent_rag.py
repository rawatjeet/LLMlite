"""
RAG Agent (Retrieval-Augmented Generation)

Answers questions about a codebase or document collection by:
  1. Indexing    - Reads all files and splits them into searchable chunks
  2. Retrieving  - Finds the most relevant chunks for a user question
  3. Generating  - Feeds retrieved context to the LLM for a grounded answer

Unlike other agents that blindly read entire files, this one retrieves
only the relevant portions, making it effective for large codebases
where reading everything would exceed the context window.

The retrieval uses TF-IDF keyword matching (no external vector DB needed),
keeping the project dependency-free.

Usage:
    python agent_rag.py
    python agent_rag.py --task "How does the agent loop work?"
    python agent_rag.py --task "What tools are available?" --top-k 5
    python agent_rag.py --directory . --extensions .py .md --verbose
"""

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    raise RuntimeError(
        "Missing dependency: python-dotenv\n"
        "Install it by running: pip install -r requirements.txt"
    )

import os
import re
import sys
import math
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter
from litellm import completion

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))
DEFAULT_TOP_K = 5
DEFAULT_CHUNK_SIZE = 40  # lines per chunk
DEFAULT_CHUNK_OVERLAP = 10  # overlapping lines between chunks


# ---------------------------------------------------------------------------
# Chunking — split files into searchable segments
# ---------------------------------------------------------------------------

def chunk_file(file_path: str, chunk_size: int, overlap: int) -> List[Dict]:
    """
    Split a file into overlapping line-based chunks.

    Each chunk is a dict with:
        file: source file path
        start_line: 1-based start line number
        end_line: 1-based end line number
        content: the text
    """
    try:
        text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    lines = text.splitlines()
    if not lines:
        return []

    chunks = []
    step = max(chunk_size - overlap, 1)

    for start in range(0, len(lines), step):
        end = min(start + chunk_size, len(lines))
        chunk_lines = lines[start:end]
        chunks.append({
            "file": file_path,
            "start_line": start + 1,
            "end_line": end,
            "content": "\n".join(chunk_lines),
        })
        if end >= len(lines):
            break

    return chunks


def index_directory(
    directory: str,
    extensions: List[str],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
    verbose: bool = False,
) -> List[Dict]:
    """Index all matching files in a directory into chunks."""
    root = Path(directory)
    all_chunks = []
    files_indexed = 0

    for ext in extensions:
        for file_path in sorted(root.rglob(f"*{ext}")):
            rel = str(file_path.relative_to(root))

            if any(part.startswith(".") for part in file_path.parts):
                continue
            if "__pycache__" in str(file_path):
                continue

            size = file_path.stat().st_size
            if size > 500_000 or size == 0:
                continue

            chunks = chunk_file(str(file_path), chunk_size, overlap)
            if chunks:
                all_chunks.extend(chunks)
                files_indexed += 1
                if verbose:
                    print(f"  Indexed: {rel} ({len(chunks)} chunks)")

    print(f"  Indexed {files_indexed} files -> {len(all_chunks)} chunks")
    return all_chunks


# ---------------------------------------------------------------------------
# TF-IDF Retrieval (no external dependencies)
# ---------------------------------------------------------------------------

def tokenize(text: str) -> List[str]:
    """Simple word tokenizer: lowercase, alphanumeric words only."""
    return re.findall(r"[a-z_][a-z0-9_]*", text.lower())


def build_idf(chunks: List[Dict]) -> Dict[str, float]:
    """Compute inverse document frequency for all terms."""
    n = len(chunks)
    doc_freq: Counter = Counter()

    for chunk in chunks:
        terms = set(tokenize(chunk["content"]))
        for term in terms:
            doc_freq[term] += 1

    idf = {}
    for term, df in doc_freq.items():
        idf[term] = math.log((n + 1) / (df + 1)) + 1  # smoothed IDF
    return idf


def tfidf_score(query_tokens: List[str], chunk: Dict, idf: Dict[str, float]) -> float:
    """Compute TF-IDF similarity between a query and a chunk."""
    chunk_tokens = tokenize(chunk["content"])
    if not chunk_tokens:
        return 0.0

    tf = Counter(chunk_tokens)
    max_tf = max(tf.values())

    score = 0.0
    for token in query_tokens:
        if token in tf:
            normalized_tf = 0.5 + 0.5 * (tf[token] / max_tf)
            score += normalized_tf * idf.get(token, 1.0)

    return score


def retrieve(
    query: str, chunks: List[Dict], idf: Dict[str, float], top_k: int = DEFAULT_TOP_K
) -> List[Dict]:
    """Find the top-k most relevant chunks for a query."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return chunks[:top_k]

    scored = []
    for chunk in chunks:
        score = tfidf_score(query_tokens, chunk, idf)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


# ---------------------------------------------------------------------------
# RAG generation
# ---------------------------------------------------------------------------

RAG_SYSTEM = """You are a knowledgeable assistant that answers questions based on retrieved context.

Rules:
1. Base your answer ONLY on the provided context chunks.
2. If the context doesn't contain enough information, say so honestly.
3. Cite which file(s) and line numbers your answer comes from.
4. Be specific and detailed in your answer.
5. If code is relevant, include short code snippets.
"""


def generate_answer(
    question: str,
    retrieved_chunks: List[Dict],
    model: str = DEFAULT_MODEL,
    verbose: bool = False,
) -> str:
    """Generate a grounded answer using retrieved chunks as context."""
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks):
        header = f"[Source {i+1}: {chunk['file']} lines {chunk['start_line']}-{chunk['end_line']}]"
        context_parts.append(f"{header}\n{chunk['content']}")

    context = "\n\n---\n\n".join(context_parts)

    user_msg = f"Question: {question}\n\nRetrieved context:\n\n{context}"

    if verbose:
        print(f"\n[Context length: {len(context)} chars from {len(retrieved_chunks)} chunks]\n")

    resp = completion(
        model=model,
        messages=[
            {"role": "system", "content": RAG_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=DEFAULT_MAX_TOKENS,
    )
    return resp.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Interactive RAG loop
# ---------------------------------------------------------------------------

def run_rag_agent(
    directory: str = ".",
    extensions: List[str] = None,
    task: Optional[str] = None,
    top_k: int = DEFAULT_TOP_K,
    model: str = DEFAULT_MODEL,
    verbose: bool = False,
) -> None:
    if extensions is None:
        extensions = [".py", ".md", ".txt"]

    print("\n" + "=" * 70)
    print("  RAG AGENT (Retrieval-Augmented Generation)")
    print("=" * 70)
    print(f"Directory : {Path(directory).resolve()}")
    print(f"Extensions: {', '.join(extensions)}")
    print(f"Model     : {model}")
    print(f"Top-K     : {top_k}\n")

    # Phase 1: Index
    print("Phase 1: INDEXING")
    print("-" * 40)
    chunks = index_directory(directory, extensions, verbose=verbose)
    if not chunks:
        print("  No files found to index. Check directory and extensions.")
        return

    # Build search index
    print("\n  Building search index...")
    idf = build_idf(chunks)
    print(f"  Vocabulary: {len(idf)} unique terms\n")

    # Phase 2: Query loop
    if task:
        questions = [task]
    else:
        print("Phase 2: ASK QUESTIONS")
        print("-" * 40)
        print("Ask questions about the codebase. Type 'exit' to quit.\n")
        questions = None

    iteration = 0
    while True:
        if questions:
            if iteration >= len(questions):
                break
            question = questions[iteration]
            iteration += 1
        else:
            try:
                question = input("Question: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nDone.")
                break
            if not question or question.lower() in ("exit", "quit"):
                break

        print(f"\n  Searching for relevant chunks...")

        # Phase 2a: Retrieve
        retrieved = retrieve(question, chunks, idf, top_k)

        print(f"  Found {len(retrieved)} relevant chunks:")
        for i, chunk in enumerate(retrieved):
            preview = chunk["content"][:80].replace("\n", " ")
            print(f"    {i+1}. {chunk['file']} (L{chunk['start_line']}-{chunk['end_line']}): {preview}...")

        # Phase 2b: Generate
        print(f"\n  Generating answer...\n")
        answer = generate_answer(question, retrieved, model, verbose)

        print(f"{'=' * 70}")
        print(f"  ANSWER")
        print(f"{'=' * 70}")
        print(f"\n{answer}\n")
        print(f"{'=' * 70}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="RAG Agent - Retrieval-Augmented Generation over local files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent_rag.py
  python agent_rag.py --task "How does the agent loop work?"
  python agent_rag.py --task "What tools are available?" --top-k 8
  python agent_rag.py --directory . --extensions .py .md
  python agent_rag.py --verbose

Pattern:
  Index files -> Retrieve relevant chunks -> Generate grounded answer
  The answer cites specific files and line numbers.
""",
    )
    parser.add_argument("--task", type=str, help="Question to answer")
    parser.add_argument("--directory", type=str, default=".", help="Directory to index")
    parser.add_argument("--extensions", nargs="+", default=[".py", ".md", ".txt"])
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of chunks to retrieve")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("No API key found. Set GEMINI_API_KEY or OPENAI_API_KEY in .env")
        return 1

    try:
        run_rag_agent(
            directory=args.directory,
            extensions=args.extensions,
            task=args.task,
            top_k=args.top_k,
            model=args.model,
            verbose=args.verbose,
        )
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1
    except Exception as e:
        print(f"\nFailed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
