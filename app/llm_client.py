"""
llm_client.py — Supports two LLM backends: Gemini (cloud) and Ollama (local).

Switch between them by setting LLM_PROVIDER in your .env file:

    LLM_PROVIDER=gemini    → uses Google Gemini (requires GEMINI_API_KEY)
    LLM_PROVIDER=ollama    → uses a local Ollama model (no API key needed)

Ollama model is configured via OLLAMA_MODEL (default: llama3.2).
"""

import json
import os

import ollama as ollama_sdk
from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.models import RCAResponse
from app.prompts import SYSTEM_PROMPT, build_user_message

# Load variables from .env into the environment at import time
load_dotenv()


# ---------------------------------------------------------------------------
# Gemini backend
# ---------------------------------------------------------------------------

def _analyze_with_gemini(user_message: str) -> str:
    """Send the ticket to Gemini and return raw text response."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. "
            "Add it to your .env file: GEMINI_API_KEY=your_key_here"
        )

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",  # Force JSON output
                response_schema=RCAResponse,
            ),
        )
    except Exception as exc:
        raise Exception(f"Gemini API call failed: {exc}") from exc

    return response.text.strip()


# ---------------------------------------------------------------------------
# Ollama backend
# ---------------------------------------------------------------------------

def _analyze_with_ollama(user_message: str) -> str:
    """Send the ticket to a local Ollama model and return raw text response."""
    model = os.getenv("OLLAMA_MODEL", "llama3.2")

    try:
        response = ollama_sdk.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            format="json",   # Tells Ollama to constrain output to JSON
            options={"temperature": 0.2},
        )
    except Exception as exc:
        raise Exception(
            f"Ollama API call failed: {exc}\n"
            f"Make sure Ollama is running (`ollama serve`) and the model "
            f"'{model}' is pulled (`ollama pull {model}`)."
        ) from exc

    return response["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Shared parsing + validation
# ---------------------------------------------------------------------------

def _parse_and_validate(raw_output: str, provider: str) -> dict:
    """Parse JSON string and check all required fields are present."""
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{provider} did not return valid JSON.\n"
            f"Raw output was:\n{raw_output}"
        ) from exc

    required_keys = {
        "tracking_id",
        "location",
        "issue_type",
        "incident_summary",
        "observed_facts",
        "hypotheses",
        "missing_evidence",
        "recommended_actions",
        "prevention_measures",
        "draft_support_response",
        "overall_confidence",
    }
    missing = required_keys - data.keys()
    if missing:
        raise ValueError(
            f"{provider} response is missing required fields: {missing}\n"
            f"Raw output was:\n{raw_output}"
        )

    return data


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def analyze_ticket(raw_text: str) -> dict:
    """
    Send a raw support ticket to the configured LLM and return the parsed RCA dict.

    Provider is selected via LLM_PROVIDER in .env:
        gemini  → Google Gemini (cloud, requires GEMINI_API_KEY)
        ollama  → Local Ollama model (no API key, requires `ollama serve`)

    Args:
        raw_text: The raw logistics ticket or error log string.

    Returns:
        A dict with keys: tracking_id, location, issue_type,
        evidence-aware analysis, actions, prevention, and a draft response.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    user_message = build_user_message(raw_text)

    if provider == "ollama":
        raw_output = _analyze_with_ollama(user_message)
    else:
        # Default to Gemini
        raw_output = _analyze_with_gemini(user_message)

    return _parse_and_validate(raw_output, provider)
