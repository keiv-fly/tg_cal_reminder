"""Simple localisation messages used across the bot."""

from __future__ import annotations

DEFAULT_LANG = "en"

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "secret_prompt": "Please provide a secret",
        "language_prompt": "Send /lang <code> to choose your language.",
        "language_set": "Language changed to {language}.",
        "help": (
            "/add_event <event_line> – add event\n"
            "/list_events [username] – list events\n"
            "/close_event <id …> – close events\n"
            "/lang <code> – change language"
        ),
        "unknown_command": "Unknown command. Send /help for usage.",
    },
    "fr": {
        "secret_prompt": "Veuillez fournir le secret",
        "language_prompt": "Envoyez /lang <code> pour choisir votre langue.",
        "language_set": "La langue a été définie sur {language}.",
        "help": (
            "/add_event <ligne> – ajouter un événement\n"
            "/list_events [utilisateur] – lister les événements\n"
            "/close_event <id …> – clôturer des événements\n"
            "/lang <code> – changer de langue"
        ),
        # Intentionally omit 'unknown_command' to test fallback
    },
    "ru": {
        "secret_prompt": "Пожалуйста, отправьте секретное слово",
        "language_prompt": "Отправьте /lang <code> чтобы выбрать язык.",
        "language_set": "Язык изменен на {language}.",
        "help": (
            "/add_event <событие> – добавить событие\n"
            "/list_events [пользователь] – список событий\n"
            "/close_event <id …> – закрыть события\n"
            "/lang <code> – изменить язык"
        ),
    },
}


def get_message(key: str, lang: str) -> str:
    """Return the message for ``key`` in ``lang`` falling back to English."""
    return MESSAGES.get(lang, MESSAGES[DEFAULT_LANG]).get(key, MESSAGES[DEFAULT_LANG].get(key, key))
