"""Provide reusable sanitizers for entity metadata payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Tuple, cast

EntityDict = Dict[str, Any]
EntityMapping = Mapping[str, Any]
OptionalFieldRule = Tuple[str, Callable[[Any], bool]]


@dataclass(frozen=True, slots=True)
class EntitySchema:
    """Describe validation rules consumed by :class:`EntitySanitizer`."""

    allowed_types: Iterable[str] = field(default_factory=tuple)
    optional_fields: Mapping[str, Tuple[OptionalFieldRule, ...]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:  # pragma: no cover - dataclass internals
        object.__setattr__(self, "allowed_types", frozenset(self.allowed_types))
        normalized = {
            key: tuple(rules)
            for key, rules in self.optional_fields.items()
        }
        object.__setattr__(self, "optional_fields", normalized)


class EntitySanitizer:
    """Sanitize entity payloads using a declarative :class:`EntitySchema`."""

    def __init__(self, schema: EntitySchema) -> None:
        self._schema = schema

    def sanitize(self, entities: Any, length: int) -> List[EntityDict]:
        """Return sanitized message entities limited by the given length."""

        limit = _normalize_limit(length)
        return _sanitize_collection(entities, limit, self._schema)


def _sanitize_collection(
        entities: Any, limit: int, schema: EntitySchema
) -> List[EntityDict]:
    """Return sanitized entity objects extracted from ``entities`` input."""

    if not isinstance(entities, list):
        return []

    sanitized: List[EntityDict] = []
    for entity in entities:
        data = _sanitize_entity(entity, limit, schema)
        if data is not None:
            sanitized.append(data)
    return sanitized


def _sanitize_entity(
        entity: Any, limit: int, schema: EntitySchema
) -> EntityDict | None:
    """Sanitize a single entity mapping, returning ``None`` if invalid."""

    if not isinstance(entity, dict):
        return None

    kind_value = entity.get("type")
    if kind_value not in schema.allowed_types:
        return None

    kind = cast(str, kind_value)
    span = _extract_span(entity, limit)
    if span is None:
        return None

    offset, length = span
    payload: EntityDict = {"type": kind, "offset": offset, "length": length}
    payload.update(_collect_optional_fields(kind, entity, schema))
    return payload


def _extract_span(entity: EntityMapping, limit: int) -> Tuple[int, int] | None:
    """Extract a valid ``(offset, length)`` pair constrained by ``limit``."""

    try:
        offset = int(entity.get("offset"))
        span = int(entity.get("length"))
    except (TypeError, ValueError):
        return None

    if offset < 0 or span < 1:
        return None

    if offset + span > limit:
        return None

    return offset, span


def _collect_optional_fields(
        kind: str, entity: EntityMapping, schema: EntitySchema
) -> EntityDict:
    """Collect optional attributes recognised for the provided entity kind."""

    extracted: EntityDict = {}
    rules = schema.optional_fields.get(kind, ())
    for field, predicate in rules:
        value = entity.get(field)
        if predicate(value):
            extracted[field] = value
    return extracted


def _normalize_limit(length: int) -> int:
    """Return a non-negative integer limit derived from ``length`` argument."""

    try:
        return max(0, int(length))
    except (TypeError, ValueError):
        return 0


__all__ = ["EntitySanitizer", "EntitySchema", "OptionalFieldRule"]

