from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Sequence, Tuple, Type, TypeVar

from pydantic import ValidationError
from pymongo import ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection

from mongoz.core.utils.cursors import closing_cursor
from mongoz.exceptions import InvalidKeyError

if TYPE_CHECKING:
    from mongoz.core.db.documents import Document
    from mongoz.core.db.querysets.expressions import Expression

DocumentT = TypeVar("DocumentT", bound="Document")


@dataclass(frozen=True)
class ValidatedUpdate:
    """A validated partial update in model and MongoDB storage namespaces."""

    attributes: Dict[str, Any]
    storage: Dict[str, Any]


def dump_document(document: Document) -> Dict[str, Any]:
    """Serialize declared model fields using their MongoDB aliases.

    Hydration accepts undeclared fields so Mongoz can read schemaless MongoDB data and
    lookup projections. Normal modeled writes do not persist those extras implicitly;
    callers that intentionally need dynamic storage can use the native collection API.
    """
    return document.model_dump(
        by_alias=True,
        include=set(type(document).model_fields),
        exclude={"id"},
    )


def get_or_create_values(expressions: Sequence[Expression]) -> Dict[str, Any]:
    """Extract only equality predicates that MongoDB can safely persist on insert.

    Comparison, regex, logical, and raw operator predicates remain lookup-only. MongoDB
    may use equality predicates from an upsert filter when constructing a new document,
    so Mongoz validates and supplies that same unambiguous subset explicitly.
    """
    values: Dict[str, Any] = {}
    for expression in expressions:
        if expression.operator != "$eq" or expression.key.startswith("$"):
            continue
        if expression.key in values and values[expression.key] != expression.compiled_value:
            raise InvalidKeyError(
                f"Conflicting equality predicates for get_or_create field {expression.key!r}"
            )
        values[expression.key] = expression.compiled_value
    return values


async def get_or_create_document(
    model_class: Type[DocumentT],
    collection: AsyncCollection[Dict[str, Any]],
    expressions: Sequence[Expression],
    defaults: Mapping[Any, Any],
    driver_options: Mapping[str, Any],
) -> DocumentT:
    """Atomically find or insert using distinct lookup and creation documents."""
    from mongoz.core.db.querysets.expressions import Expression

    lookup = Expression.compile_many(list(expressions))
    normalized_defaults = {
        (key if isinstance(key, str) else key._name): value for key, value in defaults.items()
    }
    allowed_fields = set(model_class.model_fields)
    allowed_fields.update(
        field.alias for field in model_class.model_fields.values() if field.alias is not None
    )
    lookup_equalities = get_or_create_values(expressions)
    invalid_equalities = set(lookup_equalities).difference(allowed_fields)
    if invalid_equalities:
        names = ", ".join(sorted(invalid_equalities))
        raise InvalidKeyError(
            f"get_or_create equality predicates must use direct declared fields: {names}"
        )
    equality_values = {
        key: value for key, value in lookup_equalities.items() if key not in {"_id", "id"}
    }
    creation_values = {**normalized_defaults, **equality_values}
    try:
        candidate = model_class(**creation_values)
    except ValidationError:
        existing = await collection.find_one(lookup, **driver_options)
        if existing is not None:
            return model_class.from_row(existing, from_collection=collection)
        raise
    model = await collection.find_one_and_update(
        lookup,
        {"$setOnInsert": dump_document(candidate)},
        upsert=True,
        return_document=ReturnDocument.AFTER,
        **driver_options,
    )
    if model is None:  # pragma: no cover - PyMongo guarantees AFTER for a successful upsert.
        from mongoz.exceptions import DocumentNotFound

        raise DocumentNotFound()
    return model_class.from_row(model, from_collection=collection)


async def patch_many(
    model_class: Type[Document],
    collection: AsyncCollection[Dict[str, Any]],
    expressions: Sequence[Expression],
    values: Mapping[str, Any],
    driver_options: Mapping[str, Any],
) -> Tuple[ValidatedUpdate, List[Any]]:
    """Validate a patch, capture candidate ids, and apply one bounded atomic update-many."""
    from mongoz.core.db.querysets.expressions import Expression

    update = validate_update_values(model_class, values)
    filter_query = Expression.compile_many(list(expressions))
    cursor = collection.find(filter_query, {"_id": 1}, **driver_options)
    async with closing_cursor(cursor):
        identifiers = [document["_id"] async for document in cursor]
    if identifiers:
        bounded_filter: Dict[str, Any] = {"_id": {"$in": identifiers}}
        if filter_query:
            bounded_filter = {"$and": [filter_query, bounded_filter]}
        await collection.update_many(bounded_filter, {"$set": update.storage}, **driver_options)
    return update, identifiers


def validate_update_values(
    model_class: Type[Document], values: Mapping[str, Any]
) -> ValidatedUpdate:
    """Validate a partial update against all inherited fields and their aliases.

    Pydantic's assignment validator is the canonical validation owner here. It preserves
    declared constraints and field validators without manufacturing a second model whose
    fields can drift from the document class.
    """
    aliases: Dict[str, str] = {}
    for field_name, field in model_class.model_fields.items():
        aliases[field_name] = field_name
        if field.alias:
            aliases[field.alias] = field_name

    normalized: Dict[str, Any] = {}
    for supplied_name, value in values.items():
        field_name = aliases.get(supplied_name)
        if field_name is None or field_name == "id":
            raise InvalidKeyError(
                f"Unknown or immutable update field {supplied_name!r} for {model_class.__name__}"
            )
        if field_name in normalized:
            raise InvalidKeyError(f"Update field {field_name!r} was supplied more than once")
        normalized[field_name] = value

    candidate = model_class.model_construct(**normalized)
    for field_name, value in normalized.items():
        mongoz_field = model_class.meta.fields.get(field_name)
        if mongoz_field is not None:
            value = mongoz_field.validate_field_value(value)
        model_class.__pydantic_validator__.validate_assignment(candidate, field_name, value)

    attributes = {field_name: getattr(candidate, field_name) for field_name in normalized}
    storage = candidate.model_dump(by_alias=True, include=set(normalized))
    return ValidatedUpdate(attributes=attributes, storage=storage)
