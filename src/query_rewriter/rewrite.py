"""Query rewriting strategies: multi-query, HyDE, step-back and synonym expansion."""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from .errors import RewriteError
from .llm import LLMPort, Message
from .prompts import PROMPTS

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

Strategy = Literal["original", "multi_query", "hyde", "step_back", "synonyms"]
EventHandler = Callable[[dict[str, object]], None]

MAX_QUERY_CHARS = 2000
MAX_REPLY_CHARS = 20_000
_MAX_HINT_CHARS = 200
_MAX_STEP_BACK_CHARS = 300
_MAX_TOKENS_LIMIT = 32_768
_MAX_TERMS_LIMIT = 1000
_MAX_SYNONYM_KEYS = 10_000
_MAX_SYNONYMS_PER_KEY = 100
_MAX_SYNONYM_CHARS = 200

_NUMBERING = re.compile(r"^\s*(?:\d{1,2}[.)]|[-*])\s+")
_WORD = re.compile(r"\w+")


@dataclass(frozen=True)
class Rewrite:
    """One query variant.

    Attributes:
        strategy: Strategy that produced the text.
        text: The rewritten query or passage.
    """

    strategy: Strategy
    text: str


@dataclass(frozen=True)
class RewriteResult:
    """Outcome of a rewrite call.

    Attributes:
        query: The normalised original query.
        rewrites: The original query first, then the generated rewrites.
        truncated: True when any reply, item or item count was cut to a limit.
    """

    query: str
    rewrites: tuple[Rewrite, ...]
    truncated: bool


def _check_int(name: str, value: object, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise RewriteError("invalid_argument", f"{name} must be an integer from {low} to {high}")
    return value


def _normalize_query(query: object) -> str:
    if not isinstance(query, str):
        raise RewriteError("invalid_argument", "query must be a string")
    if len(query) > MAX_QUERY_CHARS:
        raise RewriteError("input_too_large", f"query exceeds {MAX_QUERY_CHARS} characters")
    normalized = " ".join(query.split())
    if not normalized:
        raise RewriteError("invalid_argument", "query must not be empty")
    return normalized


def _normalize_hint(hint: object) -> str:
    if hint is None:
        return "general"
    if not isinstance(hint, str):
        raise RewriteError("invalid_argument", "domain_hint must be a string or None")
    if len(hint) > _MAX_HINT_CHARS:
        raise RewriteError("input_too_large", f"domain_hint exceeds {_MAX_HINT_CHARS} characters")
    normalized = " ".join(hint.split())
    if not normalized:
        raise RewriteError("invalid_argument", "domain_hint must not be empty")
    return normalized


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fold(text: str) -> str:
    return " ".join(text.casefold().split())


def _dedup_key(text: str) -> str:
    folded = text.casefold()
    kept = "".join(ch for ch in folded if not unicodedata.category(ch).startswith("P"))
    return " ".join(kept.split())


def _messages(user: str) -> list[Message]:
    return [
        {"role": "system", "content": PROMPTS["system"]},
        {"role": "user", "content": user},
    ]


def _prompt_lines(messages: Sequence[Message]) -> frozenset[str]:
    lines: set[str] = set()
    for message in messages:
        for line in message["content"].splitlines():
            stripped = line.strip()
            if stripped:
                lines.add(stripped)
    return frozenset(lines)


def _complete(llm: LLMPort, messages: list[Message], max_tokens: int) -> str:
    reply = llm.complete(messages, max_tokens=max_tokens)
    if not isinstance(reply, str):
        raise RewriteError("unparseable_output", "model reply is not text")
    return reply


def _unfence(text: str) -> str:
    stripped = text.strip()
    if len(stripped) >= 6 and stripped.startswith("```") and stripped.endswith("```"):
        inner = stripped[3:-3]
        if "\n" in inner:
            inner = inner.split("\n", 1)[1]
        return inner.strip()
    return stripped


def _json_items(body: str) -> list[str] | None:
    if not body.startswith("["):
        return None
    try:
        data = json.loads(body)
    except (ValueError, RecursionError):
        return None
    if not isinstance(data, list):
        return None
    return [item for item in data if isinstance(item, str)]


def _line_items(body: str) -> list[str]:
    items: list[str] = []
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            continue
        cleaned = _NUMBERING.sub("", line, count=1).strip()
        if cleaned:
            items.append(cleaned)
    return items


def _candidates(reply: str) -> tuple[list[str], bool]:
    truncated = len(reply) > MAX_REPLY_CHARS
    text = reply[:MAX_REPLY_CHARS]
    if not text.strip():
        raise RewriteError("empty_output", "model reply is empty")
    body = _unfence(text)
    found = _json_items(body)
    if found is None:
        found = _line_items(body)
    stripped = (item.strip() for item in found)
    items = [item for item in stripped if item]
    if not items:
        raise RewriteError("unparseable_output", "no rewrites found in model reply")
    return items, truncated


def _select(
    items: Sequence[str],
    original: str,
    prompt_lines: frozenset[str],
    n: int,
    max_len: int,
) -> tuple[list[str], bool]:
    seen = {_dedup_key(original)}
    selected: list[str] = []
    truncated = False
    for raw in items:
        if raw in prompt_lines:
            continue
        text = raw
        if len(text) > max_len:
            text = text[:max_len].rstrip()
            truncated = True
        key = _dedup_key(text)
        if not key or key in seen:
            continue
        seen.add(key)
        selected.append(text)
    if len(selected) > n:
        del selected[n:]
        truncated = True
    return selected, truncated


def _emit(
    on_event: EventHandler | None,
    strategy: Strategy,
    reply_chars: int,
    items: int,
    truncated: bool,
) -> None:
    if on_event is None:
        return
    payload: dict[str, object] = {
        "strategy": strategy,
        "reply_chars": reply_chars,
        "items": items,
        "truncated": truncated,
    }
    try:
        on_event(payload)
    except Exception:
        logger.warning("on_event callback failed for strategy %s", strategy)


def _finish(
    strategy: Strategy,
    original: str,
    selected: list[str],
    truncated: bool,
    reply_chars: int,
    on_event: EventHandler | None,
) -> RewriteResult:
    rewrites = [Rewrite("original", original)]
    rewrites.extend(Rewrite(strategy, text) for text in selected)
    logger.debug("rewrite %s: items=%d truncated=%s", strategy, len(selected), truncated)
    _emit(on_event, strategy, reply_chars, len(selected), truncated)
    return RewriteResult(original, tuple(rewrites), truncated)


def multi_query(
    llm: LLMPort,
    query: str,
    *,
    n: int = 3,
    max_len: int = 300,
    max_tokens: int = 400,
    on_event: EventHandler | None = None,
) -> RewriteResult:
    """Ask the model for up to ``n`` alternative phrasings of ``query``.

    The reply is parsed as a JSON array of strings or as lines, de-duplicated
    and capped. The first rewrite of the result is always the original query.

    Raises:
        RewriteError: ``invalid_argument``, ``input_too_large``, ``empty_output``
            or ``unparseable_output``. Exceptions of ``llm`` propagate unchanged.
    """
    original = _normalize_query(query)
    count = _check_int("n", n, 1, 10)
    limit = _check_int("max_len", max_len, 1, MAX_QUERY_CHARS)
    tokens = _check_int("max_tokens", max_tokens, 1, _MAX_TOKENS_LIMIT)
    user = PROMPTS["multi_query"].format(n=count, query=_escape(original))
    messages = _messages(user)
    reply = _complete(llm, messages, tokens)
    items, truncated = _candidates(reply)
    selected, cut = _select(
        items,
        original,
        _prompt_lines(messages),
        count,
        limit,
    )
    return _finish(
        "multi_query",
        original,
        selected,
        truncated or cut,
        len(reply),
        on_event,
    )


def hyde(
    llm: LLMPort,
    query: str,
    *,
    max_chars: int = 1200,
    domain_hint: str | None = None,
    max_tokens: int = 600,
    on_event: EventHandler | None = None,
) -> RewriteResult:
    """Generate a hypothetical passage that answers ``query`` (Gao et al. 2022, HyDE).

    Reference: Precise Zero-Shot Dense Retrieval without Relevance Labels.

    Raises:
        RewriteError: ``invalid_argument``, ``input_too_large`` or ``empty_output``.
            Exceptions of ``llm`` propagate unchanged.
    """
    original = _normalize_query(query)
    limit = _check_int("max_chars", max_chars, 1, MAX_REPLY_CHARS)
    tokens = _check_int("max_tokens", max_tokens, 1, _MAX_TOKENS_LIMIT)
    hint = _normalize_hint(domain_hint)
    user = PROMPTS["hyde"].format(
        max_chars=limit,
        domain_hint=_escape(hint),
        query=_escape(original),
    )
    messages = _messages(user)
    reply = _complete(llm, messages, tokens)
    passage = reply[:MAX_REPLY_CHARS].strip()
    if not passage:
        raise RewriteError("empty_output", "model reply is empty")
    selected, cut = _select(
        [passage],
        original,
        _prompt_lines(messages),
        1,
        limit,
    )
    return _finish(
        "hyde",
        original,
        selected,
        cut or len(reply) > MAX_REPLY_CHARS,
        len(reply),
        on_event,
    )


def step_back(
    llm: LLMPort,
    query: str,
    *,
    max_tokens: int = 100,
    on_event: EventHandler | None = None,
) -> RewriteResult:
    """Ask for one more general question behind ``query`` (Zheng et al. 2023).

    Reference: Take a Step Back: Evoking Reasoning via Abstraction in Large
    Language Models.

    Raises:
        RewriteError: ``invalid_argument``, ``input_too_large``, ``empty_output``
            or ``unparseable_output``. Exceptions of ``llm`` propagate unchanged.
    """
    original = _normalize_query(query)
    tokens = _check_int("max_tokens", max_tokens, 1, _MAX_TOKENS_LIMIT)
    user = PROMPTS["step_back"].format(query=_escape(original))
    messages = _messages(user)
    reply = _complete(llm, messages, tokens)
    items, truncated = _candidates(reply)
    selected, cut = _select(
        items,
        original,
        _prompt_lines(messages),
        1,
        _MAX_STEP_BACK_CHARS,
    )
    return _finish(
        "step_back",
        original,
        selected,
        truncated or cut,
        len(reply),
        on_event,
    )


def _build_table(synonyms: Mapping[str, Sequence[str]]) -> dict[tuple[str, ...], list[str]]:
    if not isinstance(synonyms, Mapping):
        raise RewriteError("invalid_argument", "synonyms must be a mapping")
    if len(synonyms) > _MAX_SYNONYM_KEYS:
        raise RewriteError("input_too_large", f"synonyms exceed {_MAX_SYNONYM_KEYS} keys")
    table: dict[tuple[str, ...], list[str]] = {}
    for key, values in synonyms.items():
        if not isinstance(key, str) or isinstance(values, str) or not isinstance(values, Sequence):
            raise RewriteError("invalid_argument", "synonyms must map strings to sequences")
        if len(key) > MAX_QUERY_CHARS or len(values) > _MAX_SYNONYMS_PER_KEY:
            raise RewriteError("input_too_large", "a synonym entry is too large")
        words = tuple(_WORD.findall(key.casefold()))
        if not words:
            continue
        cleaned: list[str] = []
        for value in values:
            if not isinstance(value, str):
                raise RewriteError("invalid_argument", "synonym values must be strings")
            if len(value) > _MAX_SYNONYM_CHARS:
                raise RewriteError("input_too_large", "a synonym is too long")
            term = " ".join(value.split())
            if term:
                cleaned.append(term)
        table.setdefault(words, []).extend(cleaned)
    return table


def _matched_keys(
    tokens: list[str],
    table: dict[tuple[str, ...], list[str]],
) -> list[tuple[str, ...]]:
    by_first: dict[str, list[tuple[str, ...]]] = {}
    for words in table:
        by_first.setdefault(words[0], []).append(words)
    candidates: list[tuple[int, int, tuple[str, ...]]] = []
    for start, token in enumerate(tokens):
        for words in by_first.get(token, []):
            if tuple(tokens[start : start + len(words)]) == words:
                candidates.append((start, len(words), words))
    order = {words: index for index, words in enumerate(table)}

    def rank(item: tuple[int, int, tuple[str, ...]]) -> tuple[int, int, int, int]:
        start, length, words = item
        return (-length, -sum(len(word) for word in words), order[words], start)

    candidates.sort(key=rank)
    used = [False] * len(tokens)
    chosen: list[tuple[int, tuple[str, ...]]] = []
    for start, length, words in candidates:
        if any(used[start : start + length]):
            continue
        for index in range(start, start + length):
            used[index] = True
        chosen.append((start, words))
    chosen.sort(key=lambda match: match[0])
    ordered: list[tuple[str, ...]] = []
    for _, words in chosen:
        if words not in ordered:
            ordered.append(words)
    return ordered


def expand_with_synonyms(
    query: str,
    synonyms: Mapping[str, Sequence[str]],
    *,
    max_terms: int = 10,
) -> RewriteResult:
    """Append synonyms of whole-word key matches to ``query``; no model is called.

    Matching is case-insensitive on the whitespace-normalised query, longest key
    first and non-overlapping. Synonyms are appended once each, in order of
    appearance of their key, up to ``max_terms``; the original terms are kept.

    Raises:
        RewriteError: ``invalid_argument`` or ``input_too_large``.
    """
    original = _normalize_query(query)
    limit = _check_int("max_terms", max_terms, 1, _MAX_TERMS_LIMIT)
    table = _build_table(synonyms)
    tokens = _WORD.findall(original.casefold())
    unique: list[str] = []
    seen: set[str] = set()
    for words in _matched_keys(tokens, table):
        for term in table[words]:
            folded = _fold(term)
            if folded not in seen:
                seen.add(folded)
                unique.append(term)
    terms = unique[:limit]
    truncated = len(unique) > limit
    rewrites = [Rewrite("original", original)]
    if terms:
        rewrites.append(Rewrite("synonyms", " ".join([original, *terms])))
    return RewriteResult(original, tuple(rewrites), truncated)
