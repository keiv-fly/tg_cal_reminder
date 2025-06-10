import httpx

COMMANDS = [
    {"command": "start", "description": "Begin conversation"},
    {"command": "lang", "description": "Change language"},
    {"command": "add_event", "description": "Add a calendar event"},
    {"command": "list_events", "description": "List user events"},
    {"command": "list_all_events", "description": "List events in range"},
    {"command": "close_event", "description": "Close events"},
    {"command": "help", "description": "Show help"},
]


async def register_commands(client: httpx.AsyncClient) -> None:
    """Register bot commands with Telegram."""
    await client.post("setMyCommands", json={"commands": COMMANDS})
