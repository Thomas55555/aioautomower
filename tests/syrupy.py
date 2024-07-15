"""Config for syrupy."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING, Any

from syrupy.extensions import AmberSnapshotExtension
from syrupy.extensions.amber import AmberDataSerializer

if TYPE_CHECKING:
    from syrupy.types import (
        PropertyFilter,
        PropertyMatcher,
        PropertyPath,
        SerializableData,
    )


class AutomowerSnapshotSerializer(AmberDataSerializer):
    """Automower snapshot serializer for Syrupy.

    Handles special cases for Automower data structures.
    """

    @classmethod
    def _serialize(  # pylint: disable=too-many-arguments
        cls,
        data: SerializableData,
        *,
        depth: int = 0,
        exclude: PropertyFilter | None = None,
        include: PropertyFilter | None = None,
        matcher: PropertyMatcher | None = None,
        path: PropertyPath = (),
        visited: set[Any] | None = None,
    ) -> str:
        """Pre-process data before serializing."""
        serializable_data = data
        if is_dataclass(data):
            serializable_data = asdict(data)

        return super()._serialize(
            serializable_data,
            depth=depth,
            exclude=exclude,
            include=include,
            matcher=matcher,
            path=path,
            visited=visited,
        )


class AutomowerSnapshotExtension(AmberSnapshotExtension):
    """AutomowerSnapshotExtension for Syrupy."""

    VERSION = "1"
    """Current version of serialization format.

    Need to be bumped when we change the AutomowerSnapshotSerializer.
    """

    serializer_class: type[AmberDataSerializer] = AutomowerSnapshotSerializer
