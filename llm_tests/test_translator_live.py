import os

import httpx
import pytest

from tg_cal_reminder.llm.translator import translate_message

if not (os.environ.get("RUN_LLM_TESTS") and os.environ.get("OPENROUTER_API_KEY")):
    pytest.skip("LLM tests disabled", allow_module_level=True)


@pytest.mark.asyncio
async def test_help_command():
    async with httpx.AsyncClient() as client:
        result = await translate_message(client, "help", "en")
    assert result.get("command") == "/help"


@pytest.mark.asyncio
async def test_add_event_command():
    text = "add event 2099-12-31 09:00 New Year Eve"
    async with httpx.AsyncClient() as client:
        result = await translate_message(client, text, "en")
    assert result.get("command") == "/add_event"
    assert result.get("args")

