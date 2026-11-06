# Usage

`query_rewriter` rewrites retrieval queries through a tiny LLM port. It has no runtime dependencies and no vendor SDKs.

## Strategies

- `multi_query(llm, query, n=3)`: up to `n` alternative phrasings.
- `hyde(llm, query)`: a hypothetical answer passage (Gao et al. 2022, Precise Zero-Shot Dense Retrieval without Relevance Labels).
- `step_back(llm, query)`: one more general question (Zheng et al. 2023, Take a Step Back).
- `expand_with_synonyms(query, synonyms)`: deterministic expansion without a model.

Every result starts with the original query as a `Rewrite("original", ...)`.

## Prompts

`PROMPTS` exports the exact text sent to the model. The system prompt states that text inside `<query>...</query>` is data, never instructions. The query is inserted with `&`, `<` and `>` escaped, so it cannot close the delimiter.

## Parsing and limits

- Queries are limited to 2000 characters; replies are cut to 20,000 characters.
- A JSON array of strings (optionally fenced) is tried first, then lines with leading numbering or bullets removed.
- Items are cut to `max_len`, de-duplicated (casefold, punctuation removed, whitespace collapsed) and capped at `n`.
- Failures raise `RewriteError` with a `code`: `empty_output`, `unparseable_output`, `invalid_argument` or `input_too_large`. Exceptions from the LLM port propagate unchanged.

## Observability

`on_event` receives `{"strategy", "reply_chars", "items", "truncated"}` and never any query or reply text. The library logs through `logging.getLogger(__name__)` with a `NullHandler` and never logs input text.

## Testing

`RecordedLLM(replies)` replays replies in order and `FakeLLM(fn)` computes them; both record every request in `.calls`.
