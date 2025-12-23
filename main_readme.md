# LiteLLM API Test Script

A beginner-friendly Python script to test OpenAI API calls using LiteLLM with automatic retry logic and error handling.

## What This Script Does

This script helps you:

- Test your OpenAI API connection
- Handle rate limiting automatically (retries with exponential backoff)
- Practice making API calls in a safe environment
- Learn basic API error handling

## Prerequisites

Before running this script, you need:

1. **Python 3.7 or higher** - [Download Python](https://www.python.org/downloads/)
2. **An OpenAI API key** - [Get one here](https://platform.openai.com/api-keys)
3. **Basic command line knowledge** - How to open a terminal/command prompt

## Installation

### Step 1: Clone or Download

Download this project to your computer.

### Step 2: Create a Virtual Environment (Recommended)

A virtual environment keeps your project dependencies isolated.

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

Create a file called `requirements.txt` with these contents:

```bash
litellm>=1.0.0
python-dotenv>=1.0.0
```

Then install:

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Your API Key

Create a file called `.env` in the same directory as `main.py`:

```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

⚠️ **Important**: Never share your `.env` file or commit it to git! Add it to `.gitignore`:

```bash
echo ".env" >> .gitignore
```

## Usage

### Basic Test

Run a simple test call:

```bash
python main.py
```

### Mock Mode (No API Credits Used)

Test the script without making a real API call:

```bash
python main.py --mock
```

### Use a Specific Model

```bash
python main.py --model gpt-4
```

### Allow More Retries

If you're experiencing rate limits, increase retry attempts:

```bash
python main.py --retries 5
```

### Combine Options

```bash
python main.py --model gpt-4 --retries 5
```

## Understanding the Code

### Key Functions

#### `load_api_key()`

Loads your API key from the `.env` file and validates it exists.

#### `call_with_retries()`

The heart of the script - makes API calls with automatic retry logic:

- If rate limited, waits and retries automatically
- Uses exponential backoff (waits longer each time)
- Provides clear error messages

#### `run_test_call()`

A simple wrapper that sends a test message to the API.

#### `main()`

The entry point that handles command-line arguments and orchestrates everything.

### How Exponential Backoff Works

When rate limited, the script waits:

- Attempt 1 fails → wait 1 second
- Attempt 2 fails → wait 2 seconds
- Attempt 3 fails → wait 4 seconds
- And so on...

This prevents overwhelming the API with rapid retry attempts.

## Common Issues & Solutions

### "OPENAI_API_KEY not found"

**Solution**: Make sure you have a `.env` file with your API key:

```bash
OPENAI_API_KEY=sk-your-key-here
```

### "Rate limit exceeded"

**Solutions**:

1. Check your API usage: <https://platform.openai.com/account/usage>
2. Verify your billing is set up: <https://platform.openai.com/account/billing>
3. Wait a few minutes before retrying
4. Use the `--retries` option to allow more attempts

### "Module not found" errors

**Solution**: Make sure you've installed dependencies:

```bash
pip install -r requirements.txt
```

### Virtual environment not activated

**Solution**: Activate it first:

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

## Project Structure

```bash
your-project/
│
├── main.py              # Main script
├── requirements.txt     # Python dependencies
├── .env                # Your API key (DO NOT COMMIT!)
├── .gitignore          # Tells git to ignore .env
└── README.md           # This file
```

## Available Models

Common models you can use with the `--model` flag:

- `gpt-3.5-turbo` - Fast and cost-effective (default)
- `gpt-4` - More capable, higher cost
- `gpt-4-turbo` - GPT-4 performance, faster
- `gpt-4o` - Latest multimodal model

Check [OpenAI's model documentation](https://platform.openai.com/docs/models) for the latest options.

## Cost Considerations

API calls cost money! Here are some tips:

1. **Use mock mode** (`--mock`) when testing your code
2. **Start with `gpt-3.5-turbo`** - it's cheaper than GPT-4
3. **Monitor your usage** at <https://platform.openai.com/account/usage>
4. **Set usage limits** in your OpenAI account settings

## Security Best Practices

✅ **DO:**

- Keep your API key in the `.env` file
- Add `.env` to `.gitignore`
- Use environment variables for sensitive data
- Rotate your API keys periodically

❌ **DON'T:**

- Commit `.env` files to git
- Share your API key publicly
- Hardcode API keys in your scripts
- Post your API key in forums or chat

## Next Steps

Once you're comfortable with this script, try:

1. Modifying the test message in `run_test_call()`
2. Adding more complex conversation flows
3. Building a chatbot using this as a foundation
4. Exploring other LiteLLM features

## Resources

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Python dotenv Documentation](https://pypi.org/project/python-dotenv/)
