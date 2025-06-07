from typing import Literal

from pydantic import BaseModel


class TranslatorResponse(BaseModel):
    command: (
        Literal[
            "/start",
            "/lang",
            "/add_event",
            "/list_events",
            "/list_all_events",
            "/close_event",
            "/help",
        ]
        | None
    ) = None
    args: list[str] | None = None
    error: Literal["Unrecognized"] | None = None


"""
        /start
        /lang <code>
        /add_event <YYYY-MM-DD HH:mm [YYYY-MM-DD HH:mm] title>
            Required: start date/time and title
            Optional: end date/time in brackets
            Example: /add_event 2024-05-17 14:30 Team meeting
            Example: /add_event 2024-05-17 14:30 2024-05-17 15:30 Team meeting
        /list_events [username]
        /list_all_events [<YYYY-MM-DD HH:mm> [YYYY-MM-DD HH:mm]]
            Optional: start date/time
            Optional: end date/time in brackets (requires start date/time)
            Example: /list_all_events
            Example: /list_all_events 2024-05-01 00:00
            Example: /list_all_events 2024-05-01 00:00 2024-05-31 23:59
        /close_event <id>
        /help
"""
