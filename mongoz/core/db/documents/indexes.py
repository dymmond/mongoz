from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Sequence, Tuple, Union

from pymongo.asynchronous.collection import AsyncCollection

from mongoz.core.db.datastructures import Index
from mongoz.core.utils.hashable import make_hashable
from mongoz.exceptions import IndexError

if TYPE_CHECKING:
    from pymongo.asynchronous.client_session import AsyncClientSession


class IndexAction(str, Enum):
    """The deterministic action assigned to one observed or declared index."""

    CORRECT = "already_correct"
    CREATE = "create"
    RECREATE = "recreate"
    RETAIN = "retain_unmanaged"
    CONFLICT = "name_conflict"


@dataclass(frozen=True)
class IndexPlanEntry:
    """One immutable reconciliation decision and its supporting definitions."""

    action: IndexAction
    name: str
    reason: str
    desired: Union[Index, None] = None
    existing: Union[Mapping[str, Any], None] = None


@dataclass(frozen=True)
class IndexPlan:
    """A side-effect-free index reconciliation plan."""

    entries: Tuple[IndexPlanEntry, ...]

    def actions(self, action: IndexAction) -> Tuple[IndexPlanEntry, ...]:
        """Return all entries assigned to one action."""
        return tuple(entry for entry in self.entries if entry.action is action)


def _normalized_spec(index: Mapping[str, Any]) -> Tuple[Any, Any]:
    raw_keys = tuple(index.get("key", {}).items())
    is_materialized_text = raw_keys == (("_fts", "text"), ("_ftsx", 1))
    is_text = is_materialized_text or any(value == "text" for _, value in raw_keys)
    if is_materialized_text:
        keys = tuple((name, "text") for name in index.get("weights", {}))
    else:
        keys = raw_keys
    ignored = {"background", "key", "name", "ns", "textIndexVersion", "v"}
    options: List[Tuple[str, Any]] = []
    for name, value in sorted(index.items()):
        if name in ignored or value is False or value is None:
            continue
        if is_text and name == "weights" and all(weight == 1 for weight in value.values()):
            continue
        if name == "default_language" and value == "english":
            continue
        if name == "language_override" and value == "language":
            continue
        options.append((name, make_hashable(value)))
    return keys, tuple(options)


def _desired_document(index: Index) -> Dict[str, Any]:
    return dict(index.document)


def plan_indexes(
    desired_indexes: Sequence[Index], existing_indexes: Sequence[Mapping[str, Any]]
) -> IndexPlan:
    """Compare desired and observed definitions without performing any writes."""
    existing_by_name = {str(index["name"]): index for index in existing_indexes}
    desired_names = {index.name for index in desired_indexes}
    entries: List[IndexPlanEntry] = []

    for desired in desired_indexes:
        desired_document = _desired_document(desired)
        existing = existing_by_name.get(desired.name)
        if existing is not None:
            action = (
                IndexAction.CORRECT
                if _normalized_spec(desired_document) == _normalized_spec(existing)
                else IndexAction.RECREATE
            )
            reason = (
                "declared name and specification match"
                if action is IndexAction.CORRECT
                else "declared name exists with a different specification"
            )
            entries.append(
                IndexPlanEntry(action, desired.name, reason, desired=desired, existing=existing)
            )
            continue

        equivalent = next(
            (
                observed
                for observed in existing_indexes
                if observed.get("name") != "_id_"
                and _normalized_spec(observed) == _normalized_spec(desired_document)
            ),
            None,
        )
        if equivalent is not None:
            entries.append(
                IndexPlanEntry(
                    IndexAction.CONFLICT,
                    desired.name,
                    f"equivalent specification already exists as {equivalent['name']!r}",
                    desired=desired,
                    existing=equivalent,
                )
            )
        else:
            entries.append(
                IndexPlanEntry(
                    IndexAction.CREATE,
                    desired.name,
                    "declared index is missing",
                    desired=desired,
                )
            )

    for name, existing in existing_by_name.items():
        if name in desired_names:
            continue
        reason = "driver-managed identifier index" if name == "_id_" else "not declared by model"
        entries.append(IndexPlanEntry(IndexAction.RETAIN, name, reason, existing=existing))

    return IndexPlan(tuple(entries))


async def execute_index_plan(
    collection: AsyncCollection[Dict[str, Any]],
    plan: IndexPlan,
    *,
    allow_recreate: bool = False,
    session: Union["AsyncClientSession", None] = None,
) -> None:
    """Execute creates and explicitly authorized same-name recreations only."""
    conflicts = plan.actions(IndexAction.CONFLICT)
    recreates = plan.actions(IndexAction.RECREATE)
    if conflicts:
        details = "; ".join(f"{entry.name}: {entry.reason}" for entry in conflicts)
        raise IndexError(f"Index reconciliation has unresolved name conflicts: {details}")
    if recreates and not allow_recreate:
        names = ", ".join(entry.name for entry in recreates)
        raise IndexError(
            f"Indexes require destructive same-name recreation: {names}. "
            "Pass force_drop=True to check_indexes() to authorize it."
        )

    for entry in recreates:
        await collection.drop_index(entry.name, session=session)
        assert entry.desired is not None
        await collection.create_indexes([entry.desired], session=session)

    creates = [
        entry.desired for entry in plan.actions(IndexAction.CREATE) if entry.desired is not None
    ]
    if creates:
        await collection.create_indexes(creates, session=session)
