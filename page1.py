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
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Make sure it's in your .env file!")

from litellm import completion
from typing import List, Dict


def generate_response(messages: List[Dict]) -> str:
    """Call LLM to get response"""
    response = completion(
        model=DEFAULT_MODEL,
        messages=messages,
        max_tokens=1024
    )
    return response.choices[0].message.content


messages = [
    {"role": "system", "content": "You are an expert software engineer that prefers functional programming."},
    {"role": "user", "content": "Write a function to swap the keys and values in a dictionary."}
]

response = generate_response(messages)
print(response)

# Respose of the model:

# In functional programming, we aim to write functions that are pure, that is, without side-effects, and we try to leverage functions such as `map` and `reduce` (or their equivalents) to transform data. Here's how you can write a function to swap the keys and values in a dictionary using Python in a functional style:

# ```python
# def swap_dict_keys_values(input_dict):
#     return dict(map(lambda kv: (kv[1], kv[0]), input_dict.items()))

# # Example usage
# original_dict = {'a': 1, 'b': 2, 'c': 3}
# swapped_dict = swap_dict_keys_values(original_dict)
# print(swapped_dict)  # Output will be {1: 'a', 2: 'b', 3: 'c'}
# ```

# ### Explanation

# 1. **Functional Approach**: We use `map` to apply a transformation to each element (key-value pair) of the dictionary.
# 2. **Lambda Function**: The lambda function `(lambda kv: (kv[1], kv[0]))` takes a key-value tuple and swaps their positions, effectively creating a value-key tuple.
# 3. **dict Constructor**: The `dict` constructor takes an iterable of key-value pairs (in this case, the swapped ones) and constructs a new dictionary.
# 4. **Purity**: This function does not modify the input dictionary but instead returns a new dictionary with swapped keys and values, adhering to functional programming principles.

# ### Note

# - This code assumes that the values in the original dictionary are unique and hashable, as keys in a dictionary must be unique and immutable.
# - If there are duplicate values in the input dictionary, the resulting dictionary may lose some of the original key-value pairs since the last occurrence will overwrite previous ones.
# */