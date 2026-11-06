# query-rewriter

[![PyPI version](https://img.shields.io/pypi/v/trysac-query-rewriter)](https://pypi.org/project/trysac-query-rewriter/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-query-rewriter)](LICENSE)
[![CI](https://github.com/Trysac/u019-query-rewriter/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u019-query-rewriter/actions/workflows/ci.yml)

Rewrite and expand retrieval queries with multi-query, HyDE and step-back prompts through the canonical LLM port, plus a no-model synonym expansion.

## Problem

Short or ambiguous queries miss passages that use different words. Ad hoc rewrite prompts produce unparsed, duplicated or runaway output, and a malicious query can rewrite the instructions. This library wraps multi-query, HyDE and step-back with fixed, reviewable prompts, escaped and delimited queries, robust parsing, deduplication and caps, plus a deterministic synonym expansion.

## Install

```sh
pip install trysac-query-rewriter
# or
uv add trysac-query-rewriter
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
from query_rewriter import RecordedLLM, expand_with_synonyms, multi_query

result = multi_query(RecordedLLM(["1. cheap flights\n2. low cost airfare"]), "air tickets")
print([r.text for r in result.rewrites])
# -> ['air tickets', 'cheap flights', 'low cost airfare']

result = expand_with_synonyms("new york pizza", {"pizza": ["pie"]})
print(result.rewrites[1].text)  # -> "new york pizza pie"
```

## Public API

- `multi_query(llm, query, *, n=3, max_len=300, max_tokens=400, on_event=None) -> RewriteResult`: up to `n` alternative phrasings (limits: `n` 1 to 10, `max_len` 1 to 2000, `max_tokens` 1 to 32768).
- `hyde(llm, query, *, max_chars=1200, domain_hint=None, max_tokens=600, on_event=None) -> RewriteResult`: one hypothetical passage (Gao et al. 2022). `max_chars` 1 to 20000; `domain_hint` at most 200 characters.
- `step_back(llm, query, *, max_tokens=100, on_event=None) -> RewriteResult`: one more general question (Zheng et al. 2023). Output capped at 300 characters.
- `expand_with_synonyms(query, synonyms, *, max_terms=10) -> RewriteResult`: whole-word, case-insensitive synonym append; no model call. `max_terms` 1 to 1000.
- `RewriteResult(query, rewrites, truncated)` and `Rewrite(strategy, text)`: frozen dataclasses; the first rewrite is always the original query.
- `PROMPTS`: read-only mapping of the exact prompt templates (`system`, `multi_query`, `hyde`, `step_back`).
- `LLMPort`: protocol with `complete(messages, *, max_tokens) -> str`. `RecordedLLM` and `FakeLLM` are deterministic test doubles; `RecordingExhaustedError` is raised when a `RecordedLLM` runs out of replies.
- `RewriteError` with `code` in `empty_output`, `unparseable_output`, `invalid_argument`, `input_too_large`. Exceptions raised by the LLM port propagate unchanged.
- Limits: queries over 2000 characters are rejected; replies are cut to 20000 characters (`truncated` is set); queries are whitespace-normalised; synonym tables are capped at 10000 keys, 100 values per key and 200 characters per value.
- `on_event` receives `{strategy, reply_chars, items, truncated}` and never the query or reply text.

## Why not LlamaIndex query transforms?

LlamaIndex provides query transforms inside its framework. This package is standalone, exports its prompts, and keeps parsing fully testable without a framework dependency.

## Security

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model and limits.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
