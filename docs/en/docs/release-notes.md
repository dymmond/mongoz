# Release Notes

## Unreleased

### Changed

- Rebuilt the documentation around a strict Zensical pipeline with deterministic include
  preparation, focused Start/Concept/Tutorial/Guide/Reference/Migration/Operations navigation,
  compatibility routes for established URLs, an explicitly archived Portuguese surface, and a
  distinct responsive Mongoz visual system.
- A missing acknowledged instance `delete()` now raises `DocumentNotFound`, matching the established
  missing-write contract for instance `update()` and `save()`; `post_delete` is not dispatched for a
  document that was not deleted.
- Streaming managers and querysets now preserve sort, skip, limit, projection, lookup, and session
  state. `last()` retains one raw document instead of hydrating the complete result set, and ordinary
  BSON hydration uses a measured fast path when no lookup projection is present.
- Literal string helpers now escape regex metacharacters; `Q.pattern()` remains the explicit raw
  regex escape hatch. Modeled writes serialize declared fields only, while raw query dictionaries,
  pipelines, bulk operations, native drivers, and `$where` are documented as trusted-only APIs.
- Registry cleanup preserves an in-flight body failure if close also fails. Native PyMongo timeout,
  retry, concern, topology, and error contracts remain unchanged and are covered by manifestation
  tests and production guidance.
- Removed the unused `orjson` runtime dependency. Added a private-reporting security policy,
  dependency auditing/review, CodeQL, recognized Dependabot configuration, and immutable action
  references in credential-sensitive release and benchmark workflows.
- CodSpeed benchmarks now measure individual fixed operations with explicit warmups and repeats.
  A separate informational standalone benchmark reports raw PyMongo and Mongoz end-to-end groups
  without making cross-ODM marketing claims.

- Signals now enforce their documented async-only receiver contract at registration. Dispatch is
  sequential in registration order, fail-fast, cancellation-safe, and isolated per document class.
- `run_sync()` accepts any awaitable, executes it exactly once, preserves application exceptions,
  and uses a context-aware worker thread only when the caller already has a running event loop.
- All Mongoz exceptions are exported consistently from `mongoz` and `mongoz.exceptions`; exception
  messages retain contextual fragments, and cardinality errors have useful defaults. Native
  PyMongo errors remain unwrapped.
- `Collection` is now a top-level export. `database.driver` and `collection.driver` are the
  supported native PyMongo escape hatches alongside `registry.driver`; Registry ownership is
  unchanged.
- Invalid settings imports, base classes, values, and names now raise `ImproperlyConfigured` with
  the original import or validation failure retained as the cause.
- Public query and settings validation no longer depends on Python assertions and remains active
  under `python -O`.
- Nested embedded models and callable document defaults are normalized before serialization,
  removing the remaining seven model-contract warnings without warning filters.

- Instance `update()` and query updates now validate inherited fields and aliases and write only the
  requested patch. Unknown update keys raise `InvalidKeyError`; `save()` remains the explicit
  all-modeled-fields synchronization API. Acknowledged instance writes raise `DocumentNotFound`
  when their persisted identifier no longer exists.
- `get_or_create()` now keeps operator predicates out of insertion values and performs a native
  atomic upsert while preserving duplicate-key errors.
- Index reconciliation now exposes a side-effect-free `IndexPlan`, retains unmanaged and `_id_`
  indexes, scopes all inspection/execution to the selected collection, and requires explicit
  authorization for same-name destructive recreation. An opt-in plan can label unmanaged indexes
  as deletion candidates, while a separate `drop_unmanaged=True` execution policy is required to
  delete them; `_id_` remains protected.
- `Document.aggregate()` and `Document.bulk_write()` provide session-aware, collection-targeted
  PyMongo-compatible escape hatches with native results and errors.

- Replaced Motor with native PyMongo Async. Mongoz now requires `pymongo>=4.13,<5.0`; 4.13 is
  the first release where the async API is generally available.
- `Registry` now owns one reusable `AsyncMongoClient`, provides idempotent async `close()`, supports
  `async with`, and never reopens after close.
- Native database and collection escape hatches now return PyMongo Async types. `registry.driver`
  is the owned `AsyncMongoClient`, and the server address is obtained with `await registry.address`.
- Cursor-producing paths follow PyMongo's call shapes: `find()` returns a cursor synchronously,
  while aggregation and index-listing cursor creation is awaited. Mongoz closes cursors after
  materialization, early generator close, and cancellation.
- Model construction, settings access, and JSON serialization now use supported Pydantic APIs.
  BSON `ObjectId` and signal JSON output is preserved without deprecated `json_encoders` config,
  and the warning gate rejects any reintroduced Pydantic deprecation.
- Manager and queryset construction is clone-on-write, so sibling filters, ordering, projection,
  and pagination no longer share mutable state.
- `using_session()` binds a PyMongo session to a derived manager or queryset, while document
  create/save/update/delete methods accept explicit sessions for transaction-safe instance writes.
- Invalid manager lookup operators now raise `OperatorInvalid` even when Python assertions are
  disabled.

### Migrating from Motor

- Remove Motor from application dependencies and remove Motor-specific imports or type checks.
- Remove the `event_loop` argument from `Registry(...)`. PyMongo binds an async client to the loop
  of its first network operation and raises on cross-loop use; create one Registry per application
  lifecycle instead of sharing it across loops or test-client portals.
- Close the Registry from the same application loop with `await registry.close()`, or use
  `async with Registry(...)`. A closed Registry must be replaced rather than reopened.
- Code relying on native or private Motor objects must migrate to PyMongo `AsyncMongoClient`,
  `AsyncDatabase`, `AsyncCollection`, and async cursor types. Motor-only private attributes and
  loop monkey-patches are no longer available.
- Import-time index I/O from `autogenerate_index=True` is no longer performed because it would bind
  the reusable client to a temporary import-time loop. Run `await registry.document_checks()` in
  async application startup and `await registry.close()` during shutdown.

### API compatibility before 1.0

Mongoz remains pre-1.0, but public API corrections follow these rules:

- Unsafe or internally contradictory behavior is fixed directly when the documented contract was
  already clear. Rejecting synchronous signal receivers and preventing `run_sync()` retries are
  bug fixes of this kind.
- A valid public API that is renamed or replaced should keep a deprecated alias and an actionable
  warning for a reasonable migration window before removal.
- Corrections to private attributes or previously undocumented internals require migration notes,
  not indefinite compatibility shims. Existing `_db` and `_collection` attributes remain usable in
  this release, but new code should use `database.driver` and `collection.driver`.
- Native PyMongo exceptions and results are compatibility boundaries and are not wrapped merely to
  make Mongoz errors look uniform.

## 0.13.3

### Fixed

- Fix the filter query method, handle the reference field validation.

## 0.13.2

### Fixed

- Fix the filter query method, revmoved the hard-coded values.

## 0.13.1

### Added

- Add the query support for the embedded documents and refrenced fields.


## 0.13.0

### Added

- Support for Python 3.14.

### Fixed

- Fix the internals where Python 3.14 annotations are evaluated differently.

## 0.12.0

### Changed

- Optimized the decimal validation code and include the precision validation.
- New internal settings for MongoZ removing the dependency of dymmond-settings and keep the
`pydantic-settings`.

## 0.11.8

### Added

- Precision validation into decimal field.
- Include test cases to verify the functionality.

### Fixed

- Optimized the decimal field validation code.

## 0.11.7

### Added

- Add field validation.

## 0.11.6

### Added

- Add Choices the support for embedded document.

### Changed

- Officially stop the support for Python 3.9 to match the ecosystem and tooling used.
- Updated internals for mypy.

### Fixed

- Fix the circular import issues for the foreign field.

## 0.11.5

### Added

- Support for ForeignKey field allowing to pass referenced model.

## 0.11.4

### Fix

- Initialize the method to get the choice field display.
- Abstract class initialization for mapping tables with the ObjectID.
- Replace the ObjectID null field to UUID field into test cases to represent the UUID.

## 0.11.3

### Added

- ChoiceField allowing to pass tuples as optional choices.

## 0.11.2

### Added

- Add the date operator to query on date-time field.

## 0.11.1

### Fix

- Running the `.filter(...)` lookups using the ID by parsing to the proper format.

## 0.11.0

### Added

- Multi-tenancy for the handling indexes

### Changed

- Remove support for Python 3.8.
- Moved to BSD-3 License to be compliant with the remaining ecosystem.

## 0.10.8

### Added

- Support for [NullableObjectId](./reference/fields.md) allowing special object ids to
be declared in the document and null.

## 0.10.7

### Added

- Support for `startswith`, `endswith`, `istartswith` and `iendswith` filters.

### Changed

- Internal metaclasses checks for annotations.
- Code cleaning and organisations.

## 0.10.6

### Added

- Support for multi-tenancy on a document level.

## 0.10.5

### Added

- [`exists()`](./reference/querying.md#evaluation-and-writes) allowing a bounded document existence query.

## 0.10.4

### Fix

- Native `decimal.Decimal` internal convertion to `bson.decimal128.Decimal128` to updates.

## 0.10.3

### Fix

- Convert decimal to Decimal128 was causing issues for insert lists.

## 0.10.2

This was missed from the version 0.10.1

### Changed

- Update internals of embedded documents to allow arbitraty types.

## 0.10.1

### Fix

- Native `decimal.Decimal` internal convertion to `bson.decimal128.Decimal128`.

## 0.10.0

### Added

- Translations to Portuguese.

### Fixed

- Regression when specifying the `collection` name in the `Meta` class of a document.

## 0.9.0

### Added

- `create_indexes_for_multiple_databases` allowing to iterate for each document
the creating of the indexes in multiple databases.
- [Registry document checks](./reference/connections-indexes.md#registry) allowing to check beforehand all the
index changes in a document.
- [Model index checks](./guides/indexes.md#execute) to do the same checks for each document.
- [`create_indexes_for_multiple_databases()`](./tutorials/multiple-databases-indexes.md#apply-an-explicit-policy).
- [`drop_indexes_for_multiple_databases()`](./tutorials/multiple-databases-indexes.md#apply-an-explicit-policy).

### Changed

- Cleaned up logic to design indexes in the `metaclass`.

## 0.8.0

### Changed

- Internal support for `hatch` and removed the need for a `Makefile`
- Documentation references
- Add using method to QuerySet manager [#28](https://github.com/dymmond/mongoz/pull/28) by [@harshalizode](https://github.com/harshalizode).

## 0.7.0

### Added

- Support for `QuerySetManagers`. Users can now build their own custom managers
and add into the documents.
- Documentation for the [QuerySetManager](./managers.md).

### Fixed

- Validation for abstract classes with multiple `managers`.

## 0.6.0

### Changed

- New lazy loading settings working side by side with `dymmond-settings`.

## 0.5.1

### Changed

- Update internal `dymmond-settings` minimum requirement.

## 0.5.0

### Changed

**BREAKING CHANGE**

- `SETTINGS_MODULE` was renamed to `MONGOZ_SETTINGS_MODULE`.

## 0.4.1

### Added

- `unique` validation for indexing in the metaclass.

## 0.4.0

### Added

- New `run_sync` allowing to run sync operations within Mongoz.

### Changed

- Deprecating internal settings from Pydantic in favour of [Dymmond Settings](https://settings.dymmond.com).

#### Breaking changes

Mongoz now uses  [Dymmond Settings](https://settings.dymmond.com) which this simply affects the way the
settings module is loaded. Prior to version 0.4.0 it was like this:

```python
MONGOZ_SETTINGS_MODULE=...
```

**From version 0.4.0 is**:

```python
SETTINGS_MODULE=...
```

The rest remains as it. More information about [how to use it in the official documentation](https://settings.dymmond.com/#how-to-use-it_1).

## 0.3.3

### Fix

- Codec options as defaults were not loading properly.

## 0.3.2

### Fix

- Codec options for `UuidRepresentation.STANDARD`.

## 0.3.1

### Fix

- Hotfix in introduced `alias` for ids when generating metaclasses.

## 0.3.0

### Added

- `none()` added to manager.
- `none()` added to queryset.

### Changed

- `autogenerate_index` in the Meta is now defaulting to `False`.

### Fixed

- `model_dump()` for all the fields on `all()` was not populating the id.
- Internal validations when parsing results from the cursor.

## 0.2.0

### Added

- Support for `only()` query.
- Support for `defer()` query.
- Support for `values()` query.
- Support for `values_list` query.
- Support for `exclude()` query.

### Changed

- Updated documentation with new queries.
- Added [Tips and Tricks](./tips-and-tricks.md).

### Fixed

- `Q.not_` was not returning proper values and denying the query.

## 0.1.1

### Fixed

- Internal assertation for the `eq` and `neq` wasn't allowing booleans to be passed.

## 0.1.0

This is the initial release of Edgy.

### Key features

* **Document inheritance** - For those cases where you don't want to repeat yourself while maintaining integrity of the documents.
* **Abstract classes** - That's right! Sometimes you simply want a document that holds common fields that doesn't need to created as
a document in the database.
* **Meta classes** - If you are familiar with Django, this is not new to you and Mongoz offers this in the same fashion.
* **Filters** - Filter by any field you want and need.
* **Model operators** - Classic operations such as `update`, `get`, `get_or_none` and many others.
* **Indexes** - Unique indexes through meta fields.
* **Signals** - Quite useful feature if you want to "listen" to what is happening with your documents.

And a lot more you can do here.
