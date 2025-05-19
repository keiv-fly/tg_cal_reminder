import pytest

from tg_cal_reminder.i18n.messages import MESSAGES, get_message, DEFAULT_LANG


def test_messages_structure():
    assert isinstance(MESSAGES, dict)
    assert DEFAULT_LANG in MESSAGES
    assert isinstance(MESSAGES[DEFAULT_LANG], dict)


def test_get_message_known_language():
    msg = get_message("secret_prompt", "fr")
    assert msg == MESSAGES["fr"]["secret_prompt"]


def test_get_message_language_fallback():
    msg = get_message("secret_prompt", "de")
    assert msg == MESSAGES[DEFAULT_LANG]["secret_prompt"]


def test_get_message_key_fallback():
    # 'unknown_command' key is missing in French on purpose
    msg = get_message("unknown_command", "fr")
    assert msg == MESSAGES[DEFAULT_LANG]["unknown_command"]
