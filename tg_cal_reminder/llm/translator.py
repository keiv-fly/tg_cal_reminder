import json
import os
from typing import Any, cast
from datetime import datetime
import pytz
import textwrap

import httpx
from httpx import HTTPError


def get_current_time_plus3():
    tz = pytz.timezone("Etc/GMT-3")  # GMT-3 is the same as +3:00
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")


SYSTEM_PROMPT = textwrap.dedent(
    f"""
    You are a translation layer for a Telegram bot. 
    Current time: {get_current_time_plus3()}. 
    Translate the user message into one of the supported commands: 
    /start, /lang <code>, /add_event <event_line>, /list_events [username], 
    /close_event <id …>, /help. 
    Return a JSON object in English like {"command": "/help", "args": ""}. 
    If the text does not map to a known command, return {"error": "Unrecognized"}. 
    Never invent new commands

    Here is the help description of all commands:
        /start
        /lang <code>
        /add_event <YYYY-MM-DD HH:mm [YYYY-MM-DD HH:mm] title>
            Required: start date/time and title
            Optional: end date/time in brackets
            Example: /add_event 2024-05-17 14:30 Team meeting
            Example: /add_event 2024-05-17 14:30 2024-05-17 15:30 Team meeting
        /list_events [username]
        /close_event <id>
        /help
    """.strip()
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def translate_message(
    client: httpx.AsyncClient, text: str, language_code: str
) -> dict[str, Any]:
    """Translate a free-form message into a bot command via OpenRouter."""
    payload = {
        "model": "openrouter/auto",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{language_code}>>> {text}"},
        ],
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY', '')}",
        "Content-Type": "application/json",
    }

    try:
        response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        response.raise_for_status()
    except HTTPError as exc:  # pragma: no cover - network path is mocked in tests
        raise RuntimeError("LLM request failed") from exc

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except Exception as exc:  # pragma: no cover - invalid API response
        raise ValueError("Invalid LLM response") from exc

    try:
        return cast(dict[str, Any], json.loads(content))
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON returned by LLM") from exc
