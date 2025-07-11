from __future__ import annotations

import os
import re
import textwrap
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from tg_cal_reminder.db import crud
from tg_cal_reminder.db.models import Event, User


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


async def handle_timezone(ctx: CommandContext, args: str) -> str:
    zone = args.strip()
    if not zone:
        raise HandlerError("Timezone name required")
    try:
        ZoneInfo(zone)
    except Exception as exc:
        raise HandlerError("Invalid timezone") from exc
    await crud.update_user_timezone(ctx.session, ctx.user, zone)
    return f"Timezone updated to {zone}"


async def handle_add_event(ctx: CommandContext, args: str) -> str:
    start, end, title = await parse_event_line(args)
    event = await crud.create_event(ctx.session, ctx.user.id, start, title, end)
    warning = ""
    if start < datetime.now(UTC):
        warning = " (past event)"
    time_str = start.astimezone(UTC).strftime("%Y-%m-%d %H:%M")
    return f"Event {event.id} added{warning}: {time_str} {title} | id={event.id}"


async def handle_edit_event(ctx: CommandContext, args: str) -> str:
    parts = args.split(maxsplit=1)
    if len(parts) != 2 or not parts[0].isdigit():
        raise HandlerError("Invalid edit usage")
    event_id = int(parts[0])
    start, end, title = await parse_event_line(parts[1])
    updated = await crud.update_event(
        ctx.session, ctx.user.id, event_id, start, title, end
    )
    if not updated:
        raise HandlerError("Event not found")
    warning = ""
    if start < datetime.now(UTC):
        warning = " (past event)"
    time_str = start.astimezone(UTC).strftime("%Y-%m-%d %H:%M")
    return (
        f"Event {event_id} updated{warning}: {time_str} {title} | id={event_id}"
    )


def _parse_range(args: str) -> tuple[datetime | None, datetime | None]:
    parts = args.split()
    if not parts:
        return None, None
    if len(parts) not in (2, 4):
        raise HandlerError("Invalid range format")
    try:
        start = datetime.fromisoformat(" ".join(parts[0:2])).replace(tzinfo=UTC)
    except ValueError as exc:
        raise HandlerError("Invalid from datetime") from exc
    end = None
    if len(parts) == 4:
        try:
            end = datetime.fromisoformat(" ".join(parts[2:4])).replace(tzinfo=UTC)
        except ValueError as exc:
            raise HandlerError("Invalid to datetime") from exc
    return start, end


async def handle_list_all_events(ctx: CommandContext, args: str) -> str:
    start, end = _parse_range(args)
    events = await crud.list_events_between(ctx.session, ctx.user.id, start, end)
    lines = []
    for ev in events:
        end_str = ev.end_time.isoformat() if ev.end_time else "-"
        status = "closed" if ev.is_closed else "open"
        lines.append(f"{ev.id} {ev.start_time.isoformat()} {end_str} {ev.title} [{status}]")
    return "\n".join(lines)


def _date_label(dt: datetime, now: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    local = dt.astimezone(UTC)
    today = now.astimezone(UTC).date()
    diff = (local.date() - today).days
    if diff == 0:
        return "Today"
    if diff == 1:
        return "Tomorrow"
    if 0 < diff < 6:
        return local.strftime("%a")
    return local.strftime("%Y-%m-%d")


async def handle_list_events(ctx: CommandContext, args: str) -> str:
    events = await crud.list_events(ctx.session, ctx.user.id, include_closed=False)

    tz = ZoneInfo(ctx.user.timezone)
    now_local = datetime.now(tz)
    today_start_utc = (
        now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        .astimezone(UTC)
    )
    now = now_local.astimezone(UTC)
    filtered: list[Event] = []
    for ev in events:
        dt = ev.start_time
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        if dt >= today_start_utc:
            filtered.append(ev)
    events = filtered
    if not events:
        return "No events found"
    lines: list[str] = []
    current_label = None
    for ev in events:
        label = _date_label(ev.start_time, now)
        if label != current_label:
            lines.append(f"{label}:")
            current_label = label
        dt = ev.start_time
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        time_str = dt.astimezone(UTC).strftime("%H:%M")
        lines.append(f"{time_str} {ev.title} | id={ev.id}")
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
        /edit_event <id> <YYYY-MM-DD HH:mm [YYYY-MM-DD HH:mm] title>
            Replace an existing event with the new data
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
        """
    ).strip()


CommandHandler = Callable[[CommandContext, str], Awaitable[str]]

_HANDLERS: dict[str, CommandHandler] = {
    "/start": handle_start,
    "/lang": handle_lang,
    "/add_event": handle_add_event,
    "/edit_event": handle_edit_event,
    "/list_events": handle_list_events,
    "/list_all_events": handle_list_all_events,
    "/timezone": handle_timezone,
    "/close_event": handle_close_event,
    "/help": handle_help,
}


async def dispatch(
    session: AsyncSession,
    user: User,
    text: str,
    language_code: str,
    translator: Callable[[str, str, str], Awaitable[dict]] | None = None,
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
        result = await translator(text, language_code, user.timezone)
        error = result.get("error")
        if error:
            raise HandlerError(error)
        command = result.get("command", "")
        raw_args = result.get("args")
        args = " ".join(raw_args) if isinstance(raw_args, list) else raw_args or ""
    handler = _HANDLERS.get(command)
    if not handler:
        raise HandlerError("Unknown command")
    return await handler(ctx, args)
