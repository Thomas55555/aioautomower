"""Tests for asynchronous Python client for aioautomower.

run tests with `poetry run pytest --cov --cov-report term-missing`
and to update snapshots
`poetry run pytest --snapshot-update --cov --cov-report term-missing`
"""

from pathlib import Path


def load_fixture(filename: str) -> str:
    """Load a fixture."""
    path = Path(__package__) / "fixtures" / filename
    return path.read_text(encoding="utf-8")
