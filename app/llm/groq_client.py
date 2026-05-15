"""
app/llm/groq_client.py
───────────────────────
Handles all communication with the Groq API.

Responsibilities:
- Initialize the Groq client using the API key from .env
- Send a prompt and return the response text
- Handle retries if the API call fails
- Log what's happening at each step
"""

import os
from dotenv import load_dotenv
from groq import Groq
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

load_dotenv(override=True)


def get_client() -> Groq:
    """
    Creates and returns a Groq client.
    Reads GROQ_API_KEY from the .env file automatically.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. "
            "Make sure it is set in your .env file."
        )
    return Groq(api_key=api_key)



@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def generate_section(
    messages: list[dict],
    model: str = None,
    max_tokens: int = None,
    temperature: float = None,
) -> str:
    """
    Sends messages to Groq and returns the generated text.

    Args:
        messages    : list of {role, content} dicts (system + user)
        model       : Groq model to use (defaults to .env value)
        max_tokens  : max response length (defaults to .env value)
        temperature : creativity level (defaults to .env value)

    Returns:
        The generated text as a plain string.

    Retries up to 3 times if the API call fails, with
    exponential backoff (waits 2s, then 4s, then 8s).
    """
    # Use .env values as defaults if not explicitly passed
    model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    max_tokens = max_tokens or int(os.getenv("MAX_TOKENS", "2048"))
    temperature = temperature or float(os.getenv("TEMPERATURE", "0.3"))

    client = get_client()

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    # Extract the text from the response object
    return response.choices[0].message.content.strip()