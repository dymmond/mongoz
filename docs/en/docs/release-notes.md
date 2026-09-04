# Release Notes

## Unreleased

## 0.15.0

### Changed

- Raised the AnyIO compatibility baseline to 4.15.0 while retaining support for Python 3.10
  through Python 3.14.
- Updated the static-analysis baseline to ty 0.0.78.

### Security

- Restored build-once trusted publishing with immutable action pins, artifact attestation,
  least-privilege OIDC permissions, and pre-publication quality gates.

## 0.14.0

### Added

- Added session-aware aggregation and bulk-write boundaries with native PyMongo results and
  errors.
- Added inspectable index plans, explicit policies for destructive reconciliation, and protected
  unmanaged and `_id_` indexes.
- Added documented native-driver access through `registry.driver`, `database.driver`, and
  `collection.driver`, plus consistent top-level exports for public errors and `Collection`.

### Changed

- Replaced Motor with PyMongo Async and introduced an explicit Registry lifecycle. A Registry owns
  one reusable `AsyncMongoClient`, supports `async with`, closes idempotently, and does not reopen
  after closure. Mongoz now requires `pymongo>=4.13,<5.0`.
- Made managers and querysets clone-on-write, preserving filters, sort, pagination, projection,
  lookup, database, and session state without mutating sibling queries. Streaming cursors now close
  reliably, and query hydration and `last()` use lower-overhead paths for improved performance.
- Propagated sessions through queries, instance writes, transactions, aggregation, bulk writes,
  and index operations while preserving native PyMongo transaction behavior.
- Clarified persistence semantics: `update()` applies an atomic modeled patch, `save()` synchronizes
  all modeled fields, and acknowledged update, save, and delete operations raise
  `DocumentNotFound` when the persisted document is missing.
- Migrated static analysis from mypy to `ty`, including typed native-driver boundaries and the
  packaged `py.typed` marker. Modernized Pydantic integration and removed model-contract warnings
  without warning filters.
- Rebuilt the documentation with a strict Zensical pipeline, focused task-based navigation,
  preserved compatibility routes, and a dedicated
  [modernization migration guide](https://mongoz.dymmond.com/migration/modernization/).
- Signals now accept async receivers only, dispatch sequentially in registration order, fail fast,
  preserve cancellation, and remain isolated per document class. `run_sync()` accepts any
  awaitable and executes it exactly once.

### Removed

- Removed Motor, the Registry `event_loop` argument, import-time index I/O, and the unused `orjson`
  runtime dependency.

### Fixed

- Corrected literal string helpers to escape regular-expression metacharacters while retaining
  `Q.pattern()` as the explicit raw-pattern boundary.
- Corrected inherited-field and alias validation for modeled writes, atomic `get_or_create()`
  behavior, missing-write errors, query validation under `python -O`, and cleanup failure
  provenance.
- Normalized public error, settings, signal, BSON serialization, and native compatibility
  boundaries without wrapping PyMongo-owned failures.

### Security

- Hardened modeled serialization and literal query helpers, documented trusted-only raw query and
  driver boundaries, and added private vulnerability reporting, dependency review and auditing,
  CodeQL, immutable action references, and least-privilege release permissions.

### Migrating from Motor

- Remove Motor imports and dependencies, then use PyMongo `AsyncMongoClient`, `AsyncDatabase`,
  `AsyncCollection`, async cursors, and `AsyncClientSession` for native boundaries.
- Remove the `event_loop` argument from `Registry(...)`. Create one Registry per application
  lifecycle, close it on the same application loop, and replace it rather than reopening it.
- Move index reconciliation to application startup with `registry.document_checks()` or explicit
  index planning, and propagate sessions explicitly for transactional work.
- Review query reuse, update versus save behavior, missing-write handling, signal receivers, raw
  query boundaries, and native escape hatches. The
  [modernization migration guide](https://mongoz.dymmond.com/migration/modernization/) is the
  canonical step-by-step guide.

### API compatibility in the 0.x release line

- Unsafe or internally contradictory behavior is corrected directly when the documented contract
  is already clear.
- A valid public API that is renamed or replaced should retain a deprecated alias and actionable
  migration guidance for a reasonable window before removal.
- Corrections to private attributes or undocumented internals receive migration guidance rather
  than indefinite shims. Existing `_db` and `_collection` attributes remain usable, while new code
  should use `database.driver` and `collection.driver`.
- Native PyMongo exceptions and results remain compatibility boundaries and are not wrapped merely
  to make Mongoz errors look uniform.

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
