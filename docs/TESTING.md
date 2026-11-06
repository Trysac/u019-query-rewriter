# Testing

## Running

```sh
uv run pytest --cov=query_rewriter   # tests with coverage report
uv run python scripts/check.py      # every gate, as CI and the factory run it
```

## Policy

- Branch coverage of `src/query_rewriter` must stay at or above 80 %; the gate fails below it.
- Tests exercise the public API (`import query_rewriter`) and assert return values, raised exceptions and their codes.
- Tests are deterministic: they use `RecordedLLM` and `FakeLLM`, with no network and no wall clock.

## Existing tests

- `tests/test_query_rewriter.py`: the only test module present. It covers the public API: the acceptance examples from the specification (multi-query numbering and bullets, fenced JSON with deduplication, HyDE truncation and empty output, step-back numbering, synonym expansion), the prompt contents sent to the model, and error codes for invalid arguments, oversized input and LLM exceptions propagating unchanged.

## Layout

`tests/test_<module>.py` mirrors each public module. No shared `conftest.py` is present in the repository today.
