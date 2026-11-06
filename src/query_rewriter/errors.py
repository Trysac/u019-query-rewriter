"""Typed errors raised by query_rewriter."""

from __future__ import annotations

from typing import Literal

ErrorCode = Literal[
    "empty_output",
    "unparseable_output",
    "invalid_argument",
    "input_too_large",
]

_MAX_MESSAGE_CHARS = 200


class RewriteError(Exception):
    """Base error of the library.

    Attributes:
        code: Stable machine-readable error code.
    """

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message[:_MAX_MESSAGE_CHARS])
        self.code: ErrorCode = code
