"""
Quasi-Agent: AI-Powered Python Function Generator

This script acts as a "quasi-agent" that:
1. Takes a function description from the user
2. Generates the initial function code
3. Adds comprehensive documentation
4. Creates unit tests
5. Saves everything to a file

It demonstrates basic agentic behavior through multi-step LLM interactions.
"""

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    raise RuntimeError(
        "Missing dependency: python-dotenv\n"
        "Install it by running: pip install -r requirements.txt"
    )

import os
import argparse
import time
import sys
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from litellm import completion
from litellm import exceptions as litellm_exceptions

# Load environment variables
load_dotenv()

# Configuration with environment variable fallbacks
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "2048"))
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.0"))
DEFAULT_TOP_P = float(os.getenv("DEFAULT_TOP_P", "1.0"))
DEFAULT_RETRIES = int(os.getenv("DEFAULT_RETRIES", "3"))
DEFAULT_BASE_SLEEP = float(os.getenv("DEFAULT_BASE_SLEEP", "1.0"))
DEFAULT_CACHE_DIR = os.getenv("LLM_CACHE_DIR", ".llm_cache")


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

def make_cache_key(messages: List[Dict], options: Dict) -> str:
    """
    Create a unique cache key based on messages and model options.
    
    This allows us to reuse previous API responses when the exact same
    request is made, saving both time and money.
    
    Args:
        messages: The conversation messages
        options: Model configuration options
    
    Returns:
        A SHA-256 hash string to use as the cache key
    """
    key_obj = {"messages": messages, "options": options}
    key_json = json.dumps(key_obj, sort_keys=True, default=str)
    return hashlib.sha256(key_json.encode('utf-8')).hexdigest()


def read_cache(cache_dir: str, key: str) -> Optional[str]:
    """
    Read a cached response from disk.
    
    Args:
        cache_dir: Directory where cache files are stored
        key: The cache key to look up
    
    Returns:
        The cached response text, or None if not found
    """
    path = Path(cache_dir) / key
    if path.exists():
        return path.read_text(encoding='utf-8')
    return None


def write_cache(cache_dir: str, key: str, value: str) -> None:
    """
    Write a response to the cache.
    
    Args:
        cache_dir: Directory where cache files are stored
        key: The cache key to store under
        value: The response text to cache
    """
    path = Path(cache_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / key).write_text(value, encoding='utf-8')


# ============================================================================
# LLM INTERACTION
# ============================================================================

def generate_response(
    messages: List[Dict],
    model: Optional[str] = None,
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    n: int = 1,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    retries: int = DEFAULT_RETRIES,
    base_sleep: float = DEFAULT_BASE_SLEEP,
    cache_dir: Optional[str] = None,
    verbose: bool = False
) -> str:
    """
    Generate a response from the LLM with caching and retry logic.
    
    This is the core function that interacts with the AI model. It includes:
    - Automatic caching to avoid duplicate API calls
    - Retry logic with exponential backoff for rate limits
    - Flexible configuration options
    
    Args:
        messages: List of conversation messages
        model: Model identifier (e.g., "gemini/gemini-1.5-flash")
        max_tokens: Maximum tokens in the response
        temperature: Randomness (0.0 = deterministic, 1.0 = creative)
        top_p: Nucleus sampling parameter
        n: Number of responses to generate
        presence_penalty: Penalty for token presence
        frequency_penalty: Penalty for token frequency
        retries: Maximum retry attempts for rate limits
        base_sleep: Base sleep time for exponential backoff
        cache_dir: Directory for caching responses
        verbose: Whether to print debug information
    
    Returns:
        The generated response text
    
    Raises:
        RateLimitError: If rate limit exceeded after all retries
    """
    if model is None:
        model = DEFAULT_MODEL
    
    options = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "n": n,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
    }
    
    # Check cache first
    cache_key = None
    if cache_dir:
        cache_key = make_cache_key(messages, options)
        cached_value = read_cache(cache_dir, cache_key)
        if cached_value is not None:
            if verbose:
                print(f"💾 Cache hit: {cache_key[:16]}...")
            return cached_value
        elif verbose:
            print(f"🔍 Cache miss: {cache_key[:16]}...")
    
    # Build API call parameters
    llm_kwargs = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "n": n,
    }
    
    if presence_penalty is not None:
        llm_kwargs["presence_penalty"] = presence_penalty
    if frequency_penalty is not None:
        llm_kwargs["frequency_penalty"] = frequency_penalty
    
    # Retry loop with exponential backoff
    attempt = 0
    while True:
        attempt += 1
        try:
            if verbose:
                print(f"🔄 API call attempt {attempt}/{retries}...")
            
            raw_resp = completion(**llm_kwargs)
            text = raw_resp.choices[0].message.content
            
            # Cache the response
            if cache_dir and cache_key:
                write_cache(cache_dir, cache_key, text)
                if verbose:
                    print(f"💾 Cached response: {cache_key[:16]}...")
            
            return text
            
        except litellm_exceptions.RateLimitError as e:
            if verbose:
                print(f"⚠️  Rate limit error (attempt {attempt}/{retries})")
            
            if attempt >= retries:
                print(f"\n❌ Rate limit exceeded after {retries} attempts")
                print("Check your API quota and billing at your provider's dashboard")
                raise
            
            sleep_seconds = base_sleep * (2 ** (attempt - 1))
            if verbose:
                print(f"⏳ Sleeping {sleep_seconds}s before retry...")
            time.sleep(sleep_seconds)


# ============================================================================
# CODE EXTRACTION
# ============================================================================

def extract_code_block(response: str) -> str:
    """
    Extract code from markdown code blocks.
    
    The LLM often wraps code in ```python ... ``` blocks. This function
    extracts just the code, removing the markdown formatting.
    
    Args:
        response: The raw LLM response
    
    Returns:
        The extracted code, or the original response if no code block found
    """
    if '```' not in response:
        return response.strip()
    
    parts = response.split('```')
    if len(parts) < 2:
        return response.strip()
    
    code_block = parts[1].strip()
    
    # Remove language identifier (e.g., "python")
    if code_block.lower().startswith("python"):
        code_block = code_block[6:].strip()
    
    return code_block


# ============================================================================
# MAIN AGENT LOGIC
# ============================================================================

def develop_custom_function(
    model: Optional[str] = None,
    mock: bool = False,
    verbose: bool = False,
    cache_enabled: bool = True
) -> Tuple[str, str, str]:
    """
    Main quasi-agent function that orchestrates the multi-step process.
    
    This function demonstrates agentic behavior by:
    1. Maintaining conversation context across multiple LLM calls
    2. Building on previous outputs in each step
    3. Executing a predefined workflow automatically
    
    The workflow:
    Step 1: Generate initial function code
    Step 2: Add comprehensive documentation
    Step 3: Create unit tests
    Step 4: Save to file
    
    Args:
        model: The LLM model to use
        mock: If True, use mock responses instead of real API calls
        verbose: If True, print detailed progress information
        cache_enabled: If True, use caching to avoid duplicate API calls
    
    Returns:
        A tuple of (function_code, test_code, filename)
    """
    print("\n" + "=" * 70)
    print("🤖 QUASI-AGENT: AI-Powered Python Function Generator")
    print("=" * 70)
    
    # Get user input
    print("\n📝 What kind of function would you like to create?")
    print("   Examples:")
    print("   - 'calculates the factorial of a number'")
    print("   - 'checks if a string is a valid email address'")
    print("   - 'finds the longest word in a sentence'")
    print("\n💡 Your description: ", end='')
    
    function_description = input().strip()
    
    if not function_description:
        print("❌ No description provided. Exiting.")
        sys.exit(1)
    
    print(f"\n✨ Great! I'll create a function that {function_description}")
    
    # Initialize conversation with system prompt
    messages = [
        {
            "role": "system",
            "content": "You are an expert Python developer who writes clean, well-documented, "
                      "and thoroughly tested code. Always follow Python best practices and PEP 8 style guidelines."
        }
    ]
    
    cache_dir = DEFAULT_CACHE_DIR if cache_enabled else None
    
    # ========================================================================
    # STEP 1: Generate Initial Function
    # ========================================================================
    print("\n" + "-" * 70)
    print("STEP 1/3: Generating initial function...")
    print("-" * 70)
    
    messages.append({
        "role": "user",
        "content": (
            f"Write a Python function that {function_description}. "
            "Follow these requirements:\n"
            "1. Use clear, descriptive function and variable names\n"
            "2. Include type hints for parameters and return value\n"
            "3. Handle edge cases appropriately\n"
            "4. Keep the function focused on a single responsibility\n\n"
            "Output only the function code in a ```python code block```."
        )
    })
    
    initial_function = generate_response(
        messages,
        model=model,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=DEFAULT_TEMPERATURE,
        cache_dir=cache_dir,
        verbose=verbose,
    ) if not mock else "def mock_function():\n    return 'mock'"
    
    initial_function = extract_code_block(initial_function)
    
    print("\n✅ Initial function generated:")
    print("─" * 70)
    print(initial_function)
    print("─" * 70)
    
    # Add to conversation (cleaned to just show code)
    messages.append({
        "role": "assistant",
        "content": f"```python\n{initial_function}\n```"
    })
    
    # ========================================================================
    # STEP 2: Add Documentation
    # ========================================================================
    print("\n" + "-" * 70)
    print("STEP 2/3: Adding comprehensive documentation...")
    print("-" * 70)
    
    messages.append({
        "role": "user",
        "content": (
            "Add comprehensive documentation to this function:\n"
            "1. A detailed docstring with description, parameters, return value, and examples\n"
            "2. Inline comments for complex logic\n"
            "3. Document any edge cases or assumptions\n"
            "4. Follow Google or NumPy docstring style\n\n"
            "Output the complete documented function in a ```python code block```."
        )
    })
    
    documented_function = generate_response(
        messages,
        model=model,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=DEFAULT_TEMPERATURE,
        cache_dir=cache_dir,
        verbose=verbose,
    ) if not mock else initial_function + "\n# Mock documentation"
    
    documented_function = extract_code_block(documented_function)
    
    print("\n✅ Documentation added:")
    print("─" * 70)
    print(documented_function)
    print("─" * 70)
    
    messages.append({
        "role": "assistant",
        "content": f"```python\n{documented_function}\n```"
    })
    
    # ========================================================================
    # STEP 3: Generate Test Cases
    # ========================================================================
    print("\n" + "-" * 70)
    print("STEP 3/3: Creating unit tests...")
    print("-" * 70)
    
    messages.append({
        "role": "user",
        "content": (
            "Create comprehensive unittest test cases for this function:\n"
            "1. Test basic functionality with typical inputs\n"
            "2. Test edge cases (empty inputs, boundary values, etc.)\n"
            "3. Test error cases (invalid inputs, type errors, etc.)\n"
            "4. Use descriptive test method names\n"
            "5. Include docstrings for each test\n\n"
            "Output the complete test class in a ```python code block```."
        )
    })
    
    test_cases = generate_response(
        messages,
        model=model,
        max_tokens=2048,
        temperature=0.0,
        cache_dir=cache_dir,
        verbose=verbose,
    ) if not mock else (
        "import unittest\n\n"
        "class TestMock(unittest.TestCase):\n"
        "    def test_mock(self):\n"
        "        self.assertEqual(mock_function(), 'mock')\n\n"
        "if __name__ == '__main__':\n"
        "    unittest.main()"
    )
    
    test_cases = extract_code_block(test_cases)
    
    print("\n✅ Test cases created:")
    print("─" * 70)
    print(test_cases)
    print("─" * 70)
    
    # ========================================================================
    # STEP 4: Save to File
    # ========================================================================
    print("\n" + "-" * 70)
    print("STEP 4/4: Saving to file...")
    print("-" * 70)
    
    # Generate filename from description
    filename = function_description.lower()
    filename = ''.join(c for c in filename if c.isalnum() or c.isspace())
    filename = filename.replace(' ', '_')[:40] + '.py'
    
    # Combine function and tests
    final_content = (
        f'"""\n'
        f'Auto-generated function: {function_description}\n'
        f'Generated by Quasi-Agent\n'
        f'"""\n\n'
        f'{documented_function}\n\n\n'
        f'{test_cases}\n'
    )
    
    # Save to file
    output_path = Path(filename)
    output_path.write_text(final_content, encoding='utf-8')
    
    print(f"\n✅ File saved: {filename}")
    print(f"   Lines of code: {len(final_content.splitlines())}")
    print(f"   File size: {len(final_content)} bytes")
    
    return documented_function, test_cases, filename


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def validate_api_key():
    """Validate that an API key is configured."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not gemini_key and not openai_key:
        print("❌ No API key found!")
        print("\nPlease set one of the following in your .env file:")
        print("  - GEMINI_API_KEY=your-key-here")
        print("  - OPENAI_API_KEY=your-key-here")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Quasi-Agent: AI-powered Python function generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python quasi-agent.py
  python quasi-agent.py --model gemini/gemini-1.5-flash
  python quasi-agent.py --mock --verbose
  python quasi-agent.py --no-cache

Environment Variables:
  DEFAULT_MODEL          Model to use (default: gemini/gemini-1.5-flash)
  DEFAULT_MAX_TOKENS     Max tokens per response (default: 2048)
  DEFAULT_TEMPERATURE    Temperature for generation (default: 0.0)
  LLM_CACHE_DIR         Cache directory (default: .llm_cache)
  GEMINI_API_KEY        Your Gemini API key
  OPENAI_API_KEY        Your OpenAI API key
        """
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Model to use (e.g., gemini/gemini-1.5-flash, openai/gpt-4)"
    )
    
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Use mock responses instead of real API calls (for testing)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress and caching information'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable response caching'
    )
    
    args = parser.parse_args()
    
    # Validate API key (unless in mock mode)
    if not args.mock:
        validate_api_key()
    
    try:
        # Run the agent
        function_code, tests, filename = develop_custom_function(
            model=args.model,
            mock=args.mock,
            verbose=args.verbose,
            cache_enabled=not args.no_cache
        )
        
        print("\n" + "=" * 70)
        print("🎉 SUCCESS! Your function is ready to use.")
        print("=" * 70)
        print(f"\n📄 Generated file: {filename}")
        print("\nNext steps:")
        print(f"  1. Review the code: cat {filename}")
        print(f"  2. Run the tests: python {filename}")
        print(f"  3. Import and use: from {filename[:-3]} import *")
        print("\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
