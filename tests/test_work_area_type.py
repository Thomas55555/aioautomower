"""Tests for the WorkAreaType enum."""

from aioautomower.model import WorkAreaType
from aioautomower.model.model_work_areas import Type


def test_work_area_type_values() -> None:
    """Verify the public string values map to the Husqvarna API payload."""
    assert WorkAreaType.RANDOM.value == "random"
    assert WorkAreaType.SYSTEMATIC.value == "systematic"


def test_work_area_type_from_api_strings() -> None:
    """Verify lowercased values from the API payload deserialize cleanly."""
    assert WorkAreaType("systematic") is WorkAreaType.SYSTEMATIC
    assert WorkAreaType("random") is WorkAreaType.RANDOM


def test_legacy_type_alias() -> None:
    """Verify the previous Type name still resolves to the same enum."""
    assert Type is WorkAreaType
    assert Type.SYSTEMATIC is WorkAreaType.SYSTEMATIC
    assert Type.RANDOM is WorkAreaType.RANDOM
