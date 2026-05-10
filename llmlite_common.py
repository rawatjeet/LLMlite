"""
LLMlite Common Utilities

Shared helpers used by every agent in this project. Centralizes the
boilerplate that used to be duplicated across 15+ scripts:

    - .env loading
    - API key validation (Gemini OR OpenAI)
    - DEFAULT_MODEL / DEFAULT_MAX_TOKENS / DEFAULT_MAX_ITERATIONS
    - call_with_retries(): retry+exponential-backoff wrapper around litellm.completion
    - format_usage(): pretty-print token usage from a litellm response

Designed to be a tiny, pure-Python module with no dependencies beyond
litellm and python-dotenv (already required by the project).

Usage:
    from llmlite_common import (
        validate_api_key,
        DEFAULT_MODEL,
        DEFAULT_MAX_TOKENS,
        call_with_retries,
        format_usage,
    )

    validate_api_key()
    response = call_with_retries(
        model=DEFAULT_MODEL,
        messages=[{"role": "user", "content": "hello"}],
    )
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Missing dependency: python-dotenv\n"
        "Install it by running: pip install -r requirements.txt"
    ) from exc

try:
    from litellm import completion
    from litellm import exceptions as litellm_exceptions
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Missing dependency: litellm\n"
        "Install it by running: pip install -r requirements.txt"
    ) from exc


load_dotenv()


DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_TOKENS: int = int(os.getenv("DEFAULT_MAX_TOKENS", "1024"))
DEFAULT_MAX_ITERATIONS: int = int(os.getenv("DEFAULT_MAX_ITERATIONS", "10"))
DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.0"))
DEFAULT_TOP_P: float = float(os.getenv("DEFAULT_TOP_P", "1.0"))
DEFAULT_RETRIES: int = int(os.getenv("DEFAULT_RETRIES", "3"))
DEFAULT_BASE_SLEEP: float = float(os.getenv("DEFAULT_BASE_SLEEP", "1.0"))


def validate_api_key(*, exit_on_missing: bool = True) -> str:
    """
    Return the first available API key. Accepts either GEMINI_API_KEY or
    OPENAI_API_KEY so any agent runs against whichever provider the user
    has configured.

    Args:
        exit_on_missing: if True (default), prints a helpful message and
            calls sys.exit(1) when no key is found. Set to False to
            instead raise EnvironmentError (useful in tests).

    Returns:
        The API key string.
    """
    key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if key:
        return key

    msg = (
        "No API key found.\n"
        "Create a .env file in the project root with one of:\n"
        "    GEMINI_API_KEY=your-key-here     # https://makersuite.google.com/app/apikey  (free)\n"
        "    OPENAI_API_KEY=your-key-here     # https://platform.openai.com/api-keys"
    )
    if exit_on_missing:
        print(msg, file=sys.stderr)
        sys.exit(1)
    raise EnvironmentError(msg)


def call_with_retries(
    *,
    model: str = DEFAULT_MODEL,
    messages: List[Dict[str, Any]],
    max_attempts: int = DEFAULT_RETRIES,
    base_sleep: float = DEFAULT_BASE_SLEEP,
    verbose: bool = False,
    **completion_kwargs: Any,
):
    """
    Wrap litellm.completion with exponential-backoff retries on rate limits.

    Any extra keyword arguments are forwarded to litellm.completion (e.g.
    tools, max_tokens, temperature, top_p).

    Args:
        model: model name in LiteLLM format (e.g. "gemini/gemini-1.5-flash")
        messages: chat messages list
        max_attempts: how many times to try before giving up
        base_sleep: seconds for the first sleep; doubles each retry
        verbose: print attempt counters when True
        **completion_kwargs: forwarded to litellm.completion()

    Returns:
        The raw litellm response object.

    Raises:
        litellm RateLimitError if every attempt fails.
        Any other exception from litellm is re-raised after the first failure.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            if verbose:
                print(f"  [LLM call attempt {attempt}/{max_attempts}]")
            return completion(model=model, messages=messages, **completion_kwargs)
        except litellm_exceptions.RateLimitError as exc:
            if verbose:
                print(f"  RateLimitError: {exc}")
            if attempt >= max_attempts:
                raise
            sleep_seconds = base_sleep * (2 ** (attempt - 1))
            if verbose:
                print(f"  Sleeping {sleep_seconds:.1f}s before retrying...")
            time.sleep(sleep_seconds)
        except Exception:
            raise


def format_usage(response: Any) -> str:
    """
    Return a one-line summary of token usage from a litellm response.

    Returns "" if the response has no .usage attribute (some mocked/streaming
    responses).
    """
    usage = getattr(response, "usage", None)
    if not usage:
        return ""
    prompt = getattr(usage, "prompt_tokens", None) or 0
    completion_t = getattr(usage, "completion_tokens", None) or 0
    total = getattr(usage, "total_tokens", None) or (prompt + completion_t)
    return f"tokens: prompt={prompt}, completion={completion_t}, total={total}"


def get_text(response: Any) -> str:
    """Return the assistant message text from a litellm response (or '')."""
    try:
        return (response.choices[0].message.content or "").strip()
    except (AttributeError, IndexError):
        return ""


__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MAX_ITERATIONS",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_TOP_P",
    "DEFAULT_RETRIES",
    "DEFAULT_BASE_SLEEP",
    "validate_api_key",
    "call_with_retries",
    "format_usage",
    "get_text",
]
