# query-rewriter

[![PyPI version](https://img.shields.io/pypi/v/trysac-query-rewriter)](https://pypi.org/project/trysac-query-rewriter/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-query-rewriter)](LICENSE)
[![CI](https://github.com/Trysac/u019-query-rewriter/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u019-query-rewriter/actions/workflows/ci.yml)

Rewrite and expand retrieval queries with multi-query, HyDE and step-back prompts through the canonical LLM port, plus a no-model synonym expansion

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-query-rewriter
# or
uv add trysac-query-rewriter
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import query_rewriter

# normalize() trims surrounding whitespace and lower-cases the text.
print(query_rewriter.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    query_rewriter.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
