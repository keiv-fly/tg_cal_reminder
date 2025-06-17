import json

import httpx
import pytest

from tg_cal_reminder.llm import translator
from tg_cal_reminder.llm.translator import (
    OPENROUTER_URL,
    build_system_prompt,
    translate_message,
)


@pytest.mark.asyncio
async def test_translate_message_success(monkeypatch):
    """Translator returns parsed JSON from LLM on success."""
    expected = {"command": "/help", "args": []}

    monkeypatch.setattr(translator, "get_current_time", lambda tz: "2024-01-01 00:00:00 UTC")

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL(OPENROUTER_URL)
        payload = json.loads(request.content.decode())
        # Ensure system prompt and user message are included
        assert payload["messages"][0]["content"] == build_system_prompt("UTC")
        assert payload["messages"][1]["content"] == "en>>> hello"
        data = {"choices": [{"message": {"content": json.dumps(expected)}}]}
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://openrouter.ai") as client:
        result = await translate_message(client, "hello", "en", "UTC")

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


@pytest.mark.asyncio
async def test_translate_message_logging(monkeypatch):
    """Translator logs input messages and parsed result."""

    expected = {"command": "/help", "args": []}

    async def handler(request: httpx.Request) -> httpx.Response:
        data = {"choices": [{"message": {"content": json.dumps(expected)}}]}
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        class DummyLogger:
            def __init__(self) -> None:
                self.records: list[str] = []

            def info(self, msg: str, *args: object) -> None:
                self.records.append(msg % args)

        dummy = DummyLogger()
        monkeypatch.setattr(translator, "logger", dummy)

        result = await translate_message(client, "hello", "en")

    assert result == expected
    assert any("LLM request messages" in r for r in dummy.records)
    assert any("LLM parsed result" in r for r in dummy.records)
