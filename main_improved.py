"""
LiteLLM API Test Script
A beginner-friendly script to test OpenAI API calls with automatic retry logic.
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
from litellm import completion
from litellm import exceptions as litellm_exceptions


def load_api_key():
    """
    Load and validate the OpenAI API key from environment variables.
    
    Returns:
        str: The API key
    
    Raises:
        ValueError: If the API key is not found
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found!\n"
            "Please create a .env file with your API key.\n"
            "Example: OPENAI_API_KEY=sk-your-key-here"
        )
    
    return api_key


def call_with_retries(
    api_key: str,
    model: str,
    messages: list,
    max_attempts: int = 3,
    base_sleep: float = 1.0
):
    """
    Call the LiteLLM API with automatic retry logic for rate limit errors.
    
    This function implements exponential backoff: if the API returns a rate limit
    error, it waits an increasing amount of time before retrying (1s, 2s, 4s, etc.)
    
    Args:
        api_key: Your OpenAI API key
        model: The model to use (e.g., "gpt-4", "gpt-3.5-turbo")
        messages: List of message dictionaries with 'role' and 'content' keys
        max_attempts: Maximum number of retry attempts (default: 3)
        base_sleep: Base sleep time in seconds for exponential backoff (default: 1.0)
    
    Returns:
        dict: The API response object
    
    Raises:
        RateLimitError: If max retry attempts are exceeded
        Exception: For any other API errors
    """
    attempt = 0
    
    while True:
        attempt += 1
        try:
            print(f"Attempt {attempt}/{max_attempts}: Calling API...")
            response = completion(model=model, api_key=api_key, messages=messages)
            print("✓ API call successful!")
            return response
            
        except litellm_exceptions.RateLimitError as e:
            print(f"⚠ Rate limit error on attempt {attempt}/{max_attempts}")
            print(f"   Error details: {e}")
            
            if attempt >= max_attempts:
                print("\n❌ Exceeded maximum retry attempts.")
                print("   Please check:")
                print("   - Your API quota: https://platform.openai.com/account/usage")
                print("   - Your billing status: https://platform.openai.com/account/billing")
                raise
            
            # Exponential backoff: wait longer after each failure
            sleep_seconds = base_sleep * (2 ** (attempt - 1))
            print(f"   Retrying in {sleep_seconds} seconds...\n")
            time.sleep(sleep_seconds)
            
        except Exception as e:
            print(f"\n❌ Unexpected error occurred:")
            print(f"   Type: {type(e).__name__}")
            print(f"   Message: {str(e)}")
            raise


def run_test_call(api_key: str, model: str = "gpt-3.5-turbo", mock: bool = False, max_retries: int = 3):
    """
    Run a test API call to verify everything is working.
    
    Args:
        api_key: Your OpenAI API key
        model: The model to use for the test
        mock: If True, skip the real API call and return a mock response
        max_retries: Maximum number of retry attempts for rate limits
    
    Returns:
        dict: The API response (real or mocked)
    """
    messages = [
        {
            "role": "user",
            "content": "Say hello and tell me you're working correctly!"
        }
    ]
    
    if mock:
        print("🎭 Mock mode enabled - skipping real API call\n")
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hello! I'm a mock response. Everything looks good! (No real API call was made)"
                }
            }]
        }
    
    print(f"🚀 Making real API call to model: {model}\n")
    return call_with_retries(
        api_key=api_key,
        model=model,
        messages=messages,
        max_attempts=max_retries
    )


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Test LiteLLM API calls with automatic retry logic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Normal API call
  python main.py --mock             # Test without using API credits
  python main.py --model gpt-4      # Use a specific model
  python main.py --retries 5        # Allow more retry attempts
        """
    )
    
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Skip the real API call and return a mock response (for testing)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='gpt-3.5-turbo',
        help='Model to use (default: gpt-3.5-turbo)'
    )
    
    parser.add_argument(
        '--retries',
        type=int,
        default=3,
        help='Maximum retry attempts for rate limits (default: 3)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("LiteLLM API Test Script")
    print("=" * 60 + "\n")
    
    try:
        # Load API key
        api_key = load_api_key()
        print("✓ API key loaded successfully\n")
        
        # Run test call
        response = run_test_call(
            api_key=api_key,
            model=args.model,
            mock=args.mock,
            max_retries=args.retries
        )
        
        # Display response
        print("\n" + "=" * 60)
        print("API Response:")
        print("=" * 60)
        
        if args.mock:
            print(response["choices"][0]["message"]["content"])
        else:
            # Extract the assistant's message from the response
            message = response.choices[0].message.content
            print(message)
        
        print("\n✓ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
