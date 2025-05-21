from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tg_cal_reminder.bot import handlers
from tg_cal_reminder.db import crud


async def handle_update(
    update: dict,
    tg_client: httpx.AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    translator: Callable[[str, str], Awaitable[dict[str, Any]]],
) -> None:
    """Process a single Telegram update."""
    message = update.get("message")
    if not message or "text" not in message:
        return

    chat_id = message.get("chat", {}).get("id")
    if chat_id is None:
        return

    telegram_id = message.get("from", {}).get("id")
    username = message.get("from", {}).get("username")
    text = message["text"]

    async with session_factory() as session:
        user = await crud.get_user_by_telegram_id(session, telegram_id)
        if user is None:
            user = await crud.create_user(session, telegram_id, username=username)
        try:
            reply = await handlers.dispatch(session, user, text, user.language, translator)
        except handlers.HandlerError as err:
            reply = str(err)

    await tg_client.post("sendMessage", data={"chat_id": chat_id, "text": reply})
