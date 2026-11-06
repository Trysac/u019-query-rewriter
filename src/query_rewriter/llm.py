"""The canonical LLM port and deterministic test doubles."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal, NamedTuple, Protocol, TypedDict

Message = TypedDict("Message", {"role": Literal["system", "user", "assistant"], "content": str})  # noqa: UP013


class LLMPort(Protocol):
    """Minimal text-completion port implemented by the caller."""

    def complete(self, messages: Sequence[Message], *, max_tokens: int) -> str:
        """Return the model reply for ``messages``."""


class RecordingExhaustedError(Exception):
    """Raised by :class:`RecordedLLM` when every recorded reply was consumed."""

    code = "recording_exhausted"


class RecordedCall(NamedTuple):
    """One request received by a test double."""

    messages: tuple[Message, ...]
    max_tokens: int


def _check_limit(max_calls: int) -> None:
    if max_calls < 1:
        raise ValueError("max_calls must be at least 1")


def _record(
    calls: list[RecordedCall],
    limit: int,
    messages: Sequence[Message],
    max_tokens: int,
) -> None:
    snapshot = tuple(Message(role=m["role"], content=m["content"]) for m in messages)
    calls.append(RecordedCall(snapshot, max_tokens))
    if len(calls) > limit:
        del calls[0]


class RecordedLLM:
    """Replay canned replies in order and record every request in ``calls``."""

    def __init__(self, replies: Sequence[str], *, max_calls: int = 1000) -> None:
        if isinstance(replies, str):
            raise TypeError("replies must be a sequence of strings, not a string")
        _check_limit(max_calls)
        self._replies = tuple(replies)
        self._max_calls = max_calls
        self._next = 0
        self.calls: list[RecordedCall] = []

    def complete(self, messages: Sequence[Message], *, max_tokens: int) -> str:
        """Return the next recorded reply or raise :class:`RecordingExhaustedError`."""
        _record(self.calls, self._max_calls, messages, max_tokens)
        if self._next >= len(self._replies):
            raise RecordingExhaustedError("no recorded reply left")
        reply = self._replies[self._next]
        self._next += 1
        return reply


class FakeLLM:
    """Answer every request with ``fn(messages)`` and record it in ``calls``."""

    def __init__(self, fn: Callable[[Sequence[Message]], str], *, max_calls: int = 1000) -> None:
        _check_limit(max_calls)
        self._fn = fn
        self._max_calls = max_calls
        self.calls: list[RecordedCall] = []

    def complete(self, messages: Sequence[Message], *, max_tokens: int) -> str:
        """Return ``fn(messages)``."""
        _record(self.calls, self._max_calls, messages, max_tokens)
        return self._fn(messages)
