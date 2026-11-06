# Fixed prompts, escaped delimiters and defensive parsing for query rewriting

Status: accepted (generated, pending human review)

## Context

Ad hoc query rewriting prompts produce unparsed, duplicated or runaway output, and a hostile query can rewrite the instructions. Frameworks bundle such transforms, but they cannot be tested or reviewed in isolation.

## Decision

Expose the exact prompts as PROMPTS, wrap the query in <query> delimiters with &, < and > escaped, and talk to the model only through a small LLMPort protocol with recorded and fake doubles. Parse replies defensively (JSON array first, then lines), cap sizes, de-duplicate on a casefolded, punctuation-free key, and drop echoed prompt lines. Provide a deterministic synonym expansion that needs no model.

## Consequences

Behaviour is fully testable offline and prompts are reviewable. The escaping and parsing are heuristics, so a model can still return poor rewrites, but they are bounded, de-duplicated and never contain the delimiter. Users supply the LLM adapter, retrieval and embeddings are out of scope, and parsing limits are fixed constants.
