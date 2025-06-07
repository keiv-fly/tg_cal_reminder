import json

import httpx
import pytest

from tg_cal_reminder.llm.translator import OPENROUTER_URL, SYSTEM_PROMPT, translate_message


@pytest.mark.asyncio
async def test_translate_message_success(monkeypatch):
    """Translator returns parsed JSON from LLM on success."""
    expected = {"command": "/help", "args": []}

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL(OPENROUTER_URL)
        payload = json.loads(request.content.decode())
        # Ensure system prompt and user message are included
        assert payload["messages"][0]["content"] == SYSTEM_PROMPT
        assert payload["messages"][1]["content"] == "en>>> hello"
        data = {"choices": [{"message": {"content": json.dumps(expected)}}]}
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://openrouter.ai") as client:
        result = await translate_message(client, "hello", "en")

    assert result == expected


@pytest.mark.asyncio
async def test_translate_message_invalid_json(monkeypatch):
    """Translator raises ValueError on invalid JSON from LLM."""

    async def handler(request: httpx.Request) -> httpx.Response:
        data = {"choices": [{"message": {"content": "not json"}}]}
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ValueError):
            await translate_message(client, "hello", "en")


@pytest.mark.asyncio
async def test_translate_message_http_error(monkeypatch):
    """HTTP errors are converted to RuntimeError."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(RuntimeError):
            await translate_message(client, "hello", "en")
