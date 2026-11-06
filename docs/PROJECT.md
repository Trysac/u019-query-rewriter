# Project record

## Objective

Provide typed, dependency-free query rewriting for retrieval: multi-query, HyDE and step-back prompts sent through a caller-supplied LLM port, with fixed, exported prompts, delimited and escaped queries, robust reply parsing, deduplication and caps, and a deterministic synonym expansion that calls no model.

## Scope

- In scope: the public API documented in [README.md](../README.md), typed and tested.
- Out of scope: retrieval, embedding the rewrites, reranking, caching, vendor SDKs, and anything that needs runtime dependencies or I/O without an accepted ADR.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 857821 / 79002 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.9168 |

## Factory run u019 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | claude-sonnet-5-5 | yes | 2461 | 61787 | 0 | 4246 | 0.3118 |
| fix-1 | claude-sonnet-5-5 | no | 10 | 963 | 9777 | 79867 | 0.0421 |
| fix-2 | claude-sonnet-5-5 | no | 8 | 755 | 8845 | 59193 | 0.0356 |
| fix-3 | claude-sonnet-5-5 | no | 10 | 987 | 9758 | 79856 | 0.0423 |
| fix-4 | claude-sonnet-5-5 | no | 10 | 1025 | 8964 | 76750 | 0.0404 |
| fix-1 | claude-sonnet-5-5 | no | 8 | 865 | 9455 | 60894 | 0.0384 |
| fix-2 | claude-sonnet-5-5 | no | 8 | 785 | 9025 | 59952 | 0.0364 |
| fix-3 | claude-sonnet-5-5 | no | 8 | 737 | 9078 | 60886 | 0.0362 |
| fix-4 | claude-sonnet-5-5 | no | 10 | 1125 | 6107 | 79422 | 0.0345 |
| fix-1 | claude-sonnet-5-5 | no | 8 | 1878 | 16966 | 45321 | 0.0657 |
| audit | claude-sonnet-5-5 | no | 10 | 2268 | 37182 | 85475 | 0.1242 |
| fix-2 | claude-sonnet-5-5 | no | 6 | 1206 | 8181 | 41327 | 0.0367 |
| docs | claude-haiku-5-5 | no | 122075 | 4621 | 0 | 0 | 0.0726 |

Total: $0.9168. Prices: Anthropic list prices.
