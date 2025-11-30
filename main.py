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

# Read API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Make sure it's in your .env file!")

def call_with_retries(api_key: str, model: str, messages: list, max_attempts: int = 3, base_sleep: float = 1.0):
    """
    Call litellm.completion with retry/backoff for RateLimitError.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return completion(model=model, api_key=api_key, messages=messages)
        except litellm_exceptions.RateLimitError as e:
            # Friendly, actionable message for rate limiting
            print(f"RateLimitError (attempt {attempt}/{max_attempts}): {e}")
            if attempt >= max_attempts:
                print("Exceeded max retry attempts due to rate limiting. Please check your API plan, quota, and billing details: https://platform.openai.com/account/usage")
                raise
            sleep_seconds = base_sleep * (2 ** (attempt - 1))
            print(f"Sleeping for {sleep_seconds} seconds before retrying...")
            time.sleep(sleep_seconds)
        except Exception as e:
            # For all other exceptions, surface a friendly error
            print("Error while calling API:", type(e), str(e))
            raise

# Make a test API call
def main():
    parser = argparse.ArgumentParser(description="Test LiteLLM completion call (with retry & mock mode)")
    parser.add_argument('--mock', action='store_true', help='Skip the real API call and return a mock response')
    parser.add_argument('--retries', type=int, default=3, help='Max retry attempts for rate limits')
    args = parser.parse_args()

    messages = [{"role": "user", "content": "Say hello using LiteLLM"}]

    response = None
    if args.mock:
        print("Mock mode enabled — skipping real API call.")
        response = {"role": "assistant", "content": "Hello from LiteLLM (mock)!"}
    else:
        # Call with a small retry/backoff loop for rate limits
        response = call_with_retries(api_key=api_key, model="gpt-4.1", messages=messages, max_attempts=args.retries)

    if response is not None:
        print("API response:")
        print(response)

if __name__ == '__main__':
    main()
