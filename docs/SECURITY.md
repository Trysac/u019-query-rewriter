# Security notes

## Threat model

`trysac-query-rewriter` is a pure library without I/O of its own. It calls only the caller-supplied `LLMPort`.

Defended:

- **Prompt injection through the query**: the query and domain hint are wrapped in `<query>` and `<domain>` delimiters; `&`, `<` and `>` are escaped so the text cannot close the delimiter, and the system prompt states that delimited text is data, not instructions.
- **Echoed instructions**: reply lines equal to a prompt line are dropped.
- **Runaway output**: replies are cut to 20000 characters, items to `max_len`, and the number of returned rewrites to `n`.
- **Oversized input**: queries over 2000 characters and synonym entries over the documented limits raise `input_too_large`.
- **Unsafe parsing**: replies are parsed with `json.loads` and line splitting only; no `eval`, `exec` or pickle.
- **Log leakage**: no query or reply text is logged; `on_event` payloads carry only strategy, lengths, counts and the truncation flag.

Not defended:

- **Malicious model output**: the library cannot judge whether a rewrite is semantically safe or faithful; callers must treat rewrites as untrusted text.
- **Prompt injection that the model follows**: escaping is not a guarantee against a model that obeys injected instructions.
- **Callback behaviour**: exceptions from `on_event` are caught and logged as a warning; the library does not inspect what the callback does.
- **Supply chain of the caller's LLM client**: out of scope; the library has no runtime dependencies of its own.

## Publishing

Releases are published to PyPI with trusted publishing (OIDC) when available, never with a long-lived token stored in the repository.

To report a vulnerability, see [SECURITY.md](../SECURITY.md).
