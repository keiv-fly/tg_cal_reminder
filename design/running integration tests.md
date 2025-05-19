# Running Integration Tests

This project contains a small integration test that exercises the bot against a real PostgreSQL instance and mocked Telegram HTTP API. The integration test lives in the `integration_tests/` folder so that it does not run with the normal unit tests.

## Setup

1. Bring up the database defined in `docker-compose.test.yml`:

   ```bash
   docker-compose -f docker-compose.test.yml up -d
   ```

2. Install the additional test dependencies:

   ```bash
   pip install respx pytest-asyncio freezegun docker-compose
   ```

3. Enable the tests by setting an environment variable:

   ```bash
   export RUN_INTEGRATION_TESTS=1
   ```

## Running on GitHub

In your GitHub Actions workflow, add steps that start the compose file before `pytest` and shut it down afterwards. Run the suite pointing `pytest` at the integration folder:

```yaml
- name: Start test services
  run: docker-compose -f docker-compose.test.yml up -d
- name: Run integration tests
  run: |
    export RUN_INTEGRATION_TESTS=1
    pytest integration_tests -q
- name: Stop services
  run: docker-compose -f docker-compose.test.yml down
```

The default `pytest` invocation continues to run only the unit tests under `tests/`.
