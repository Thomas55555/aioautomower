"""Tests for asynchronous Python client for aioautomower.

run tests with `pytest --cov=aioautomower ./tests`
"""

from pathlib import Path


def load_fixture(filename: str) -> str:
    """Load a fixture."""
    path = Path(__package__) / "fixtures" / filename
    return path.read_text(encoding="utf-8")
