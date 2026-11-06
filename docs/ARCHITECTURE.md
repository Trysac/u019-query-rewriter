# Architecture

## Purpose

`trysac-query-rewriter` is a small, dependency-free Python library that rewrites and expands retrieval queries with multi-query, HyDE and step-back prompts through the canonical LLM port, plus a no-model synonym expansion.

## Shape

```text
caller code --> query_rewriter (public API in __init__.py)
                    |
                    +-- rewrite.py (strategies, parsing, selection)
                    +-- prompts.py (fixed PROMPTS mapping)
                    +-- llm.py (LLMPort protocol, RecordedLLM, FakeLLM)
                    +-- errors.py (RewriteError and ErrorCode)
```

- **Public API**: the names listed in `__all__` of `src/query_rewriter/__init__.py`. Anything else is internal.
- **Errors**: invalid input and unusable model output raise `RewriteError` with a stable `code`; LLM exceptions propagate unchanged.
- **Side effects**: the library calls only the caller-supplied `LLMPort`. It configures no logging (a `NullHandler` is attached) and never logs input text.

## Quality contract

`scripts/check.py` is the single definition of the gates; `fabrica.json` tells the factory and CI how to run it. See [TESTING.md](TESTING.md).

## Decisions

Architecture decisions are recorded in [decisions/](decisions/) as numbered ADRs.
