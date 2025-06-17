from typing import Literal

from pydantic import BaseModel, Field


class TranslatorResponse(BaseModel):
    does_the_user_mention_towns: bool = Field(
        default=False,
        description=(
            "Return True if the user mentions any town or city name in the message."
            ' Like "Moscow", "Paris", "New York", etc.'
        ),
    )
    related_to_changing_timezone: bool = Field(
        default=False,
        description=(
            "The user message is related to changing the timezone if he says something like "
            '"change timezone to <timezone>". In Russian it could also be said '
            '"переведи моё время в <timezone>". If the town or city name is mentioned, '
            "then it is more likely that the user wants to change the timezone."
        ),
    )
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
    error_reason: str | None = Field(
        default=None,
        description=(
            "If the user message is not related to any of the commands, then return a long "
            "explanation why it is not related to any of the commands. "
            "List all of the possible commands and explain why they are not related to the user "
            "message. The explanation should be in English."
        ),
    )
