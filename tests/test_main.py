import logging
import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from tg_cal_reminder import main as main_mod

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_main_initializes_components(monkeypatch):
    os.environ["BOT_TOKEN"] = "TOKEN"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    monkeypatch.setattr(main_mod, "get_engine", lambda: engine)
    monkeypatch.setattr(main_mod, "get_sessionmaker", lambda e: session_maker)

    handle_called = {}

    async def dummy_handle(update, tg_client, session_factory, translator):
        handle_called["called"] = True

    monkeypatch.setattr(main_mod, "handle_update", dummy_handle)
    monkeypatch.setattr(main_mod, "translate_message", lambda *a, **k: {})

    registered = {}

    async def dummy_register(client):
        registered["called"] = True

    monkeypatch.setattr(main_mod, "register_commands", dummy_register)

    class DummyScheduler:
        def __init__(self):
            self.started = False
            self.stopped = False

        def start(self):
            self.started = True

        def shutdown(self):
            self.stopped = True

    scheduler_instance = DummyScheduler()
    monkeypatch.setattr(main_mod.scheduler, "create_scheduler", lambda: scheduler_instance)

    class DummyPoller:
        def __init__(self, token, handler, *, client=None, timeout=30):
            self.token = token
            self.handler = handler
            self.run_called = False

        async def run(self):
            self.run_called = True
            await self.handler({"message": {"text": "hi", "chat": {"id": 1}, "from": {"id": 5}}})

    poller_instance = DummyPoller("TOKEN", lambda u: None)

    def poller_factory(token, handler, *, client=None, timeout=30):
        nonlocal poller_instance
        poller_instance = DummyPoller(token, handler, client=client, timeout=timeout)
        return poller_instance

    monkeypatch.setattr(main_mod, "Poller", poller_factory)

    await main_mod.main()

    assert logging.getLogger().level == logging.INFO

    assert poller_instance.run_called
    assert scheduler_instance.started and scheduler_instance.stopped
    assert handle_called.get("called") is True
    assert registered.get("called") is True

    await engine.dispose()
