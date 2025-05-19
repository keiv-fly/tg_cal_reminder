"""Telegram long polling utilities."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterable

import httpx

logger = logging.getLogger(__name__)


class Poller:
    """Simple long polling client for the Telegram Bot API."""

    def __init__(
        self,
        token: str,
        handler: Callable[[dict], Awaitable[None]],
        *,
        client: httpx.AsyncClient | None = None,
        timeout: int = 30,
    ) -> None:
        self.token = token
        self.handler = handler
        self.timeout = timeout
        base_url = f"https://api.telegram.org/bot{token}/"
        self.client = client or httpx.AsyncClient(base_url=base_url)
        self.offset: int | None = None
        self.poll_interval = 1
        self._min_interval = 1
        self._max_interval = 5

    async def get_updates(self) -> list[dict]:
        params = {"timeout": self.timeout}
        if self.offset is not None:
            params["offset"] = self.offset
        response = await self.client.get("getUpdates", params=params)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok", False):
            raise RuntimeError("Telegram API responded with failure")
        updates: Iterable[dict] = payload.get("result", [])
        return list(updates)

    async def dispatch(self, update: dict) -> None:
        try:
            await self.handler(update)
        except Exception:  # noqa: BLE001 - handler errors must not crash polling
            logger.exception("handler failed")

    async def poll_once(self) -> None:
        updates = await self.get_updates()
        if updates:
            for update in updates:
                self.offset = update["update_id"] + 1
                await self.dispatch(update)
            self.poll_interval = self._min_interval
        else:
            self.poll_interval = min(self._max_interval, self.poll_interval + 1)

    async def run(self) -> None:
        while True:
            try:
                await self.poll_once()
            except httpx.HTTPError:
                logger.exception("polling failed")
            await asyncio.sleep(self.poll_interval)
