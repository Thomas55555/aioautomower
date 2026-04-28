"""Tests for the WorkAreaType enum."""

import warnings

import pytest

from aioautomower.model import WorkArea, WorkAreaType


def test_work_area_type_values() -> None:
    """Verify the public string values map to the Husqvarna API payload."""
    assert WorkAreaType.RANDOM.value == "random"
    assert WorkAreaType.SYSTEMATIC.value == "systematic"


def test_work_area_type_from_api_strings() -> None:
    """Verify lowercased values from the API payload deserialize cleanly."""
    assert WorkAreaType("systematic") is WorkAreaType.SYSTEMATIC
    assert WorkAreaType("random") is WorkAreaType.RANDOM


@pytest.mark.parametrize(
    ("api_value", "expected"),
    [
        ("SYSTEMATIC", WorkAreaType.SYSTEMATIC),
        ("RANDOM", WorkAreaType.RANDOM),
        ("systematic", WorkAreaType.SYSTEMATIC),
        ("random", WorkAreaType.RANDOM),
        ("Systematic", WorkAreaType.SYSTEMATIC),
    ],
)
def test_work_area_deserialize_api_payload(
    api_value: str, expected: WorkAreaType
) -> None:
    """Verify the WorkArea deserializer accepts the casing variants the API sends.

    The Husqvarna Automower Connect API returns the work area type as an
    uppercase string (for example ``SYSTEMATIC``), so the dataclass deserializer
    must lowercase the value before constructing the enum. This regression test
    locks that behaviour in so the HA Core integration keeps deserializing.
    """
    payload = {
        "name": "test_area",
        "type": api_value,
        "cuttingHeight": 50,
        "useGlobalCuttingHeight": True,
        "enabled": True,
    }
    work_area = WorkArea.from_dict(payload)
    assert work_area.type is expected


def test_legacy_type_alias_emits_deprecation_warning() -> None:
    """Verify the previous Type name still resolves but warns on access."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from aioautomower.model.model_work_areas import Type  # noqa: PLC0415

        assert Type is WorkAreaType
        assert any(
            issubclass(w.category, DeprecationWarning)
            and "WorkAreaType" in str(w.message)
            for w in caught
        )


def test_legacy_type_alias_unknown_attribute() -> None:
    """Verify unknown attributes still raise AttributeError."""
    import aioautomower.model.model_work_areas as module  # noqa: PLC0415

    with pytest.raises(AttributeError):
        module.DoesNotExist  # noqa: B018
