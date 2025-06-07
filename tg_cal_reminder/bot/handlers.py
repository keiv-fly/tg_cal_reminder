from __future__ import annotations

import os
import re
import textwrap
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from tg_cal_reminder.db import crud
from tg_cal_reminder.db.models import User


def get_secret() -> str:
    """Return the secret word from environment."""
    return os.environ.get("BOT_SECRET", "open-sesame")


_EVENT_RE = re.compile(
    r"^(?P<start>\d{4}-\d{2}-\d{2} \d{2}:\d{2})"
    r"(?: (?P<end>\d{4}-\d{2}-\d{2} \d{2}:\d{2}))?"
    r" (?P<title>.+)$"
)


class HandlerError(Exception):
    """Raised when incoming command arguments are invalid."""


@dataclass
class CommandContext:
    session: AsyncSession
    user: User


async def parse_event_line(event_line: str) -> tuple[datetime, datetime | None, str]:
    match = _EVENT_RE.match(event_line)
    if not match:
        raise HandlerError("Invalid event format")

    start = datetime.fromisoformat(match.group("start")).replace(tzinfo=UTC)
    end = match.group("end")
    end_dt = None
    if end:
        end_dt = datetime.fromisoformat(end).replace(tzinfo=UTC)
    title = match.group("title")
    return start, end_dt, title


async def handle_start(ctx: CommandContext, args: str) -> str:
    return "Please provide a secret"


async def handle_lang(ctx: CommandContext, args: str) -> str:
    language = args.strip()
    if not language:
        raise HandlerError("Language code required")
    await crud.update_user_language(ctx.session, ctx.user, language)
    return f"Language updated to {language}"


async def handle_add_event(ctx: CommandContext, args: str) -> str:
    start, end, title = await parse_event_line(args)
    event = await crud.create_event(ctx.session, ctx.user.id, start, title, end)
    warning = ""
    if start < datetime.now(UTC):
        warning = " (past event)"
    return f"Event {event.id} added{warning}"


async def handle_list_events(ctx: CommandContext, args: str) -> str:
    events = await crud.list_events(ctx.session, ctx.user.id)
    lines = []
    for ev in events:
        end = ev.end_time.isoformat() if ev.end_time else "-"
        status = "closed" if ev.is_closed else "open"
        lines.append(f"{ev.id} {ev.start_time.isoformat()} {end} {ev.title} [{status}]")
    return "\n".join(lines)


async def handle_close_event(ctx: CommandContext, args: str) -> str:
    ids = [int(part) for part in args.split() if part.isdigit()]
    changed = await crud.close_events(ctx.session, ctx.user.id, ids)
    if not changed:
        return "No events closed"
    return "Closed: " + " ".join(str(i) for i in changed)


async def handle_help(ctx: CommandContext, args: str) -> str:
    return textwrap.dedent(
        """
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
        """
    ).strip()


CommandHandler = Callable[[CommandContext, str], Awaitable[str]]

_HANDLERS: dict[str, CommandHandler] = {
    "/start": handle_start,
    "/lang": handle_lang,
    "/add_event": handle_add_event,
    "/list_events": handle_list_events,
    "/close_event": handle_close_event,
    "/help": handle_help,
}


async def dispatch(
    session: AsyncSession,
    user: User,
    text: str,
    language_code: str,
    translator: Callable[[str, str], Awaitable[dict]] | None = None,
) -> str:
    ctx = CommandContext(session=session, user=user)

    if not user.is_authorized:
        if text == get_secret():
            await crud.authorize_user(session, user)
            return 'Please write your preferred language using command "/lang en"'
        if text.startswith("/start"):
            return "Please provide a secret"
        return "The secret is wrong. Please provide a secret"

    if text.startswith("/"):
        command, _, args = text.partition(" ")
    else:
        if translator is None:
            raise HandlerError("No translator provided for free text")
        result = await translator(text, language_code)
        if "error" in result:
            raise HandlerError(result["error"])
        command = result.get("command", "")
        args = result.get("args", "")
    handler = _HANDLERS.get(command)
    if not handler:
        raise HandlerError("Unknown command")
    return await handler(ctx, args)
