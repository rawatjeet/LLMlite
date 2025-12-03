try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    raise RuntimeError("Missing dependency: python-dotenv. Run 'python -m pip install -r requirements.txt' in your virtual environment.")

import os
import json
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