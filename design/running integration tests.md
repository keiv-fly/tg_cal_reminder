# Running Integration Tests

This project contains a small integration test that exercises the bot against a
mocked Telegram HTTP API and a temporary SQLite database. The integration test
lives in the `integration_tests/` folder and now runs automatically together
with the unit tests.

No external services are required. Running `pytest` will execute both the unit
and integration tests.
