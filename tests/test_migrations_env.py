import importlib
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import pytest


def load_env(monkeypatch):
    dummy_context = SimpleNamespace(
        config=SimpleNamespace(config_file_name=None),
        run_migrations=lambda: None,
        configure=lambda **_: None,
        begin_transaction=nullcontext,
        is_offline_mode=lambda: True,
    )
    alembic_module = SimpleNamespace(context=dummy_context)
    monkeypatch.setitem(sys.modules, "alembic", alembic_module)
    monkeypatch.setitem(sys.modules, "alembic.context", dummy_context)
    if "migrations.env" in sys.modules:
        del sys.modules["migrations.env"]
    return importlib.import_module("migrations.env")


def test_get_url_replaces_postgres(monkeypatch):
    env = load_env(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")
    assert env.get_url() == "postgresql+asyncpg://user:pass@localhost/db"


def test_get_url_preserves_postgresql(monkeypatch):
    env = load_env(monkeypatch)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost/db",
    )
    assert env.get_url() == "postgresql+asyncpg://user:pass@localhost/db"


def test_get_url_missing(monkeypatch):
    env = load_env(monkeypatch)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError):
        env.get_url()
