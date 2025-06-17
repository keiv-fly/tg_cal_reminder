import json
import logging
import os
import textwrap
from datetime import UTC, datetime, tzinfo
from typing import Any, cast
from zoneinfo import ZoneInfo

import httpx
from httpx import HTTPError

logger = logging.getLogger(__name__)


def get_current_time(timezone: str) -> str:
    """Return the current time in ``timezone`` formatted for the system prompt."""
    try:
        tz: tzinfo = ZoneInfo(timezone)
    except Exception:
        tz = UTC
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")


def get_current_time_utc() -> str:
    """Return the current UTC time formatted for backward compatibility."""
    return get_current_time("UTC")


PROMPT_TEMPLATE = textwrap.dedent(
    """
    You are a translation layer for a Telegram bot.
    Current time: {current_time}.
    Translate the user message into one of the supported commands:
    /start, /lang <code>, /add_event <event_line>, /edit_event <id event_line>,
    /list_events [username], /list_all_events [from to], /close_event <id …>,
    /timezone <name>, /help.
    Return a JSON object correspoding to this Pedantic model:
    ```python
    class TranslatorResponse(BaseModel):
    does_the_user_mention_towns: bool = Field(
        default=False,
        description=(
            "Return True if the user mentions any town or city name in the message."
            ' Like "Moscow", "Paris", "New York", etc.'
        ),
    )
    related_to_changing_timezone: bool = Field(
        default=False,
        description=(
            "The user message is related to changing the timezone if he says something like "
            '"change timezone to <timezone>". In Russian it could also be said '
            '"переведи моё время в <timezone>". If the town or city name is mentioned, '
            "then it is more likely that the user wants to change the timezone."
        ),
    )
    command: (
        Literal[
            "/start",
            "/lang",
            "/add_event",
            "/list_events",
            "/list_all_events",
            "/close_event",
            "/help",
        ]
        | None
    ) = None
    args: list[str] | None = None
    error: Literal["Unrecognized"] | None = None
    error_reason: str | None = Field(
        default=None,
        description=(
            "If the user message is not related to any of the commands, then return a long "
            "explanation why it is not related to any of the commands. "
            "List all of the possible commands and explain why they are not related to the user "
            "message. The explanation should be in English."
        ),
    )
    ```
    If the text does not map to a known command, return {{"error": "Unrecognized"}}.
    The answer should not contain any other text than the JSON object.
    The JSON object should begin with `{{` and end with `}}`.

    Here is the help description of all commands:
        /start
        /lang <code>
        /add_event <YYYY-MM-DD HH:mm [YYYY-MM-DD HH:mm] title>
            Required: start date/time and title
            Optional: end date/time in brackets
            Example: /add_event 2024-05-17 14:30 Team meeting
            Example: /add_event 2024-05-17 14:30 2024-05-17 15:30 Team meeting
        /edit_event <id> <YYYY-MM-DD HH:mm [YYYY-MM-DD HH:mm] title>
            Example: /edit_event 5 2024-05-17 14:30 Updated meeting
            Example: /edit_event 5 2024-05-17 14:30 2024-05-17 15:00 Updated meeting
        /list_events [username]
        /list_all_events [<YYYY-MM-DD HH:mm> [YYYY-MM-DD HH:mm]]
            Optional: start date/time
            Optional: end date/time in brackets (requires start date/time)
            Example: /list_all_events
            Example: /list_all_events 2024-05-01 00:00
            Example: /list_all_events 2024-05-01 00:00 2024-05-31 23:59
        /timezone <name>
            Example: /timezone Europe/Moscow
            Example: /timezone Europe/Paris
            Example: /timezone America/New_York
        /close_event <id>
        /help
    """.strip()
)


def build_system_prompt(timezone: str) -> str:
    """Return the system prompt for ``timezone``."""
    return PROMPT_TEMPLATE.format(current_time=get_current_time(timezone))


SYSTEM_PROMPT = build_system_prompt("UTC")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def translate_message(
    client: httpx.AsyncClient, text: str, language_code: str, timezone: str = "UTC"
) -> dict[str, Any]:
    """Translate a free-form message into a bot command via OpenRouter."""
    system_prompt = build_system_prompt(timezone)
    payload = {
        "model": "openrouter/auto",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{language_code}>>> {text}"},
        ],
        "temperature": 0,
    }
    logger.info("LLM request messages: %s", payload["messages"])
    print(payload["messages"])
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
        logger.info("LLM raw response: %s", data)
        content = data["choices"][0]["message"]["content"]
        print(content)

    except Exception as exc:  # pragma: no cover - invalid API response
        raise ValueError("Invalid LLM response") from exc

    try:
        result = cast(dict[str, Any], json.loads(content))
        logger.info("LLM parsed result: %s", result)
        return result
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON returned by LLM") from exc
