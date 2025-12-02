try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    raise RuntimeError("Missing dependency: python-dotenv. Run 'python -m pip install -r requirements.txt' in your virtual environment.")

import os
import argparse
import time
from litellm import completion
from litellm import exceptions as litellm_exceptions

# Load environment variables from .env file
load_dotenv()

# Read API key for Gemini Or OpenAI
# api_key = os.getenv("OPENAI_API_KEY")
# if not api_key:
#     raise ValueError("OPENAI_API_KEY not found. Make sure it's in your .env file!")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Make sure it's in your .env file!")

from typing import List, Dict
import sys
import hashlib
import json
from pathlib import Path

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "1024"))
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.0"))
DEFAULT_TOP_P = float(os.getenv("DEFAULT_TOP_P", "1.0"))
DEFAULT_RETRIES = int(os.getenv("DEFAULT_RETRIES", "3"))
DEFAULT_BASE_SLEEP = float(os.getenv("DEFAULT_BASE_SLEEP", "1.0"))
DEFAULT_CACHE_DIR = os.getenv("LLM_CACHE_DIR", ".llm_cache")


def _make_cache_key(messages: List[Dict], options: Dict) -> str:
   key_obj = {"messages": messages, "options": options}
   key_json = json.dumps(key_obj, sort_keys=True, default=str)
   return hashlib.sha256(key_json.encode('utf-8')).hexdigest()


def _read_cache(cache_dir: str, key: str) -> str | None:
   path = Path(cache_dir) / key
   if path.exists():
      return path.read_text(encoding='utf-8')
   return None


def _write_cache(cache_dir: str, key: str, value: str) -> None:
   path = Path(cache_dir)
   path.mkdir(parents=True, exist_ok=True)
   (path / key).write_text(value, encoding='utf-8')


def generate_response(messages: List[Dict], model: str | None = None, *,
                      max_tokens: int = DEFAULT_MAX_TOKENS,
                      temperature: float = DEFAULT_TEMPERATURE,
                      top_p: float = DEFAULT_TOP_P,
                      n: int = 1,
                      presence_penalty: float | None = None,
                      frequency_penalty: float | None = None,
                      retries: int = DEFAULT_RETRIES,
                      base_sleep: float = DEFAULT_BASE_SLEEP,
                      cache_dir: str | None = None,
                      verbose: bool = False) -> str:
   """Call LLM to get response"""
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

   # Try reading from cache first
   cache_key = None
   if cache_dir:
      cache_key = _make_cache_key(messages, options)
      cached_value = _read_cache(cache_dir, cache_key)
      if cached_value is not None:
         if verbose:
            print(f"Cache hit: {cache_key}")
         return cached_value
   # Build kwargs for the LLM client
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

   # call with retries
   def _call_llm():
      return completion(**llm_kwargs)

   attempt = 0
   while True:
      attempt += 1
      try:
         raw_resp = _call_llm()
         text = raw_resp.choices[0].message.content
         # write cache
         if cache_dir and cache_key:
            _write_cache(cache_dir, cache_key, text)
         return text
      except litellm_exceptions.RateLimitError as e:
         if verbose:
            print(f"RateLimitError (attempt {attempt}/{retries}): {repr(e)}")
         if attempt >= retries:
            raise
         sleep_seconds = base_sleep * (2 ** (attempt - 1))
         if verbose:
            print(f"Sleeping {sleep_seconds}s before retrying...")
         time.sleep(sleep_seconds)
   return response.choices[0].message.content

def extract_code_block(response: str) -> str:
   """Extract code block from response"""

   if not '```' in response:
      return response

   parts = response.split('```')
   if len(parts) < 2:
      return response
   code_block = parts[1].strip()
   # Check for "python" at the start and remove

   if code_block.startswith("python"):
      code_block = code_block[6:]

   return code_block

def develop_custom_function(model: str | None = None, mock: bool = False):
   # Get user input for function description
   print("\nWhat kind of function would you like to create?")
   print("Example: 'A function that calculates the factorial of a number'")
   print("Your description: ", end='')
   function_description = input().strip()

   # Initialize conversation with system prompt
   messages = [
      {"role": "system", "content": "You are a Python expert helping to develop a function."}
   ]

   # First prompt - Basic function
   messages.append({
      "role": "user",
      "content": f"Write a Python function that {function_description}. Output the function in a ```python code block```."
   })
   initial_function = generate_response(
      messages,
      model=model,
      max_tokens=DEFAULT_MAX_TOKENS,
      temperature=float(os.getenv("DEFAULT_TEMPERATURE", str(DEFAULT_TEMPERATURE))),
      top_p=float(os.getenv("DEFAULT_TOP_P", str(DEFAULT_TOP_P))),
      cache_dir=os.getenv("LLM_CACHE_DIR", DEFAULT_CACHE_DIR) if os.getenv("LLM_CACHE_DIR") else None,
      verbose=False,
   ) if not mock else "def mock_function():\n    return 'mock'"

   # Parse the response to get the function code
   initial_function = extract_code_block(initial_function)

   print("\n=== Initial Function ===")
   print(initial_function)

   # Add assistant's response to conversation
   # Notice that I am purposely causing it to forget its commentary and just see the code so that
   # it appears that is always outputting just code.
   messages.append({"role": "assistant", "content": "```python\n\n" + initial_function + "\n\n```"})

   # Second prompt - Add documentation
   messages.append({
      "role": "user",
      "content": "Add comprehensive documentation to this function, including description, parameters, "
                 "return value, examples, and edge cases. Output the function in a ```python code block```."
   })
   documented_function = generate_response(
      messages,
      model=model,
      max_tokens=DEFAULT_MAX_TOKENS,
      temperature=float(os.getenv("DEFAULT_TEMPERATURE", str(DEFAULT_TEMPERATURE))),
      top_p=float(os.getenv("DEFAULT_TOP_P", str(DEFAULT_TOP_P))),
      cache_dir=os.getenv("LLM_CACHE_DIR", DEFAULT_CACHE_DIR) if os.getenv("LLM_CACHE_DIR") else None,
      verbose=False,
   ) if not mock else initial_function + "\n# Mock documentation"
   documented_function = extract_code_block(documented_function)
   print("\n=== Documented Function ===")
   print(documented_function)

   # Add documentation response to conversation
   messages.append({"role": "assistant", "content": "```python\n\n" + documented_function + "\n\n```"})

   # Third prompt - Add test cases
   messages.append({
      "role": "user",
      "content": "Add unittest test cases for this function, including tests for basic functionality, "
              "edge cases, error cases, and various input scenarios. Output the code in a ```python code block```."
   })
   test_cases = generate_response(
      messages,
      model=model,
      max_tokens=512,
      temperature=0.0,
      cache_dir=os.getenv("LLM_CACHE_DIR", DEFAULT_CACHE_DIR) if os.getenv("LLM_CACHE_DIR") else None,
      verbose=False,
   ) if not mock else "import unittest\n\nclass TestMock(unittest.TestCase):\n    def test_mock(self):\n        self.assertEqual(mock_function(), 'mock')\n\nif __name__ == '__main__':\n    unittest.main()"
   # We will likely run into random problems here depending on if it outputs JUST the test cases or the
   # test cases AND the code. This is the type of issue we will learn to work through with agents in the course.
   test_cases = extract_code_block(test_cases)
   print("\n=== Test Cases ===")
   print(test_cases)

   # Generate filename from function description
   filename = function_description.lower()
   filename = ''.join(c for c in filename if c.isalnum() or c.isspace())
   filename = filename.replace(' ', '_')[:30] + '.py'

   # Save final version
   with open(filename, 'w', encoding='utf-8') as f:
      f.write(documented_function + '\n\n' + test_cases)

   return documented_function, test_cases, filename

if __name__ == "__main__":
   parser = argparse.ArgumentParser(description="Quasi-Agent: generate function and tests via LLM")
   parser.add_argument("--model", type=str, default=os.getenv("DEFAULT_MODEL", "openai/gpt-4"),
                       help="Model to use (e.g., openai/gpt-4 or gpt-4.1-nano). Can also be set via DEFAULT_MODEL env var.")
   parser.add_argument('--mock', action='store_true', help='Skip real API calls and use mock responses')
   parser.add_argument('--verbose', action='store_true', help='Show debugging output and caches')
   args = parser.parse_args()

   function_code, tests, filename = develop_custom_function(model=args.model, mock=args.mock)
   print(f"\nFinal code has been saved to {filename}")