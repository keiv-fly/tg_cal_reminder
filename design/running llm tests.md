# Running LLM Tests

These optional tests hit the real OpenRouter API to verify the translator's output.

1. Export a valid `OPENROUTER_API_KEY` environment variable.
2. Enable the suite with `RUN_LLM_TESTS=1`.
3. Run the tests:

```bash
pytest llm_tests -q
```

They are not included in the normal test run defined in `pyproject.toml`.
