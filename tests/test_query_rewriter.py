"""Behavior tests for the public API of query_rewriter."""

from __future__ import annotations

import pytest

import query_rewriter


def test_normalize_trims_and_lowercases() -> None:
    assert query_rewriter.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        query_rewriter.normalize(value)


def test_version_is_semver() -> None:
    parts = query_rewriter.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
