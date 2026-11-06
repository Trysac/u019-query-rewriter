"""Rewrite and expand retrieval queries with multi-query, HyDE, step-back and synonyms."""

from __future__ import annotations

from .errors import ErrorCode, RewriteError
from .llm import (
    FakeLLM,
    LLMPort,
    Message,
    RecordedCall,
    RecordedLLM,
    RecordingExhaustedError,
)
from .prompts import PROMPTS
from .rewrite import (
    Rewrite,
    RewriteResult,
    Strategy,
    expand_with_synonyms,
    hyde,
    multi_query,
    step_back,
)

__all__ = [
    "PROMPTS",
    "ErrorCode",
    "FakeLLM",
    "LLMPort",
    "Message",
    "RecordedCall",
    "RecordedLLM",
    "RecordingExhaustedError",
    "Rewrite",
    "RewriteError",
    "RewriteResult",
    "Strategy",
    "__version__",
    "expand_with_synonyms",
    "hyde",
    "multi_query",
    "step_back",
]

__version__ = "0.1.0"
