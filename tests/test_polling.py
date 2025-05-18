import asyncio

import httpx
import pytest

from tg_cal_reminder.bot.polling import Poller


@pytest.mark.asyncio
async def test_poll_once_no_updates_increases_interval():
    responses = [[]] * 6
    history: list[httpx.URL] = []

    async def transport_handler(request: httpx.Request) -> httpx.Response:
        history.append(request.url)
        data = {"ok": True, "result": responses[len(history) - 1]}
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(transport_handler)
    base_url = "https://api.telegram.org/botTOKEN/"
    async with httpx.AsyncClient(transport=transport, base_url=base_url) as client:
        poller = Poller("TOKEN", lambda u: asyncio.sleep(0), client=client)
        intervals = []
        for _ in range(5):
            await poller.poll_once()
            intervals.append(poller.poll_interval)
        assert intervals == [2, 3, 4, 5, 5]


@pytest.mark.asyncio
async def test_poll_once_with_updates_resets_interval_and_calls_handler():
    responses = [[{"update_id": 1, "message": {"text": "hi"}}], []]
    history: list[httpx.URL] = []
    called: list[dict] = []

    async def handler(update: dict) -> None:
        called.append(update)

    async def transport_handler(request: httpx.Request) -> httpx.Response:
        history.append(request.url)
        data = {"ok": True, "result": responses[len(history) - 1]}
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(transport_handler)
    base_url = "https://api.telegram.org/botTOKEN/"
    async with httpx.AsyncClient(transport=transport, base_url=base_url) as client:
        poller = Poller("TOKEN", handler, client=client)
        await poller.poll_once()
        assert poller.poll_interval == 1
        assert poller.offset == 2
        assert called == [{"update_id": 1, "message": {"text": "hi"}}]


@pytest.mark.asyncio
async def test_offset_passed_in_subsequent_requests():
    responses = [[{"update_id": 5}], []]
    history: list[httpx.URL] = []

    async def transport_handler(request: httpx.Request) -> httpx.Response:
        history.append(request.url)
        data = {"ok": True, "result": responses[len(history) - 1]}
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(transport_handler)
    base_url = "https://api.telegram.org/botTOKEN/"
    async with httpx.AsyncClient(transport=transport, base_url=base_url) as client:
        poller = Poller("TOKEN", lambda u: asyncio.sleep(0), client=client)
        await poller.poll_once()
        await poller.poll_once()

    assert history[0].params.get("offset") is None
    assert history[1].params.get("offset") == "6"
