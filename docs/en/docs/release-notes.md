# Release Notes

## 0.11.5

### Added

- Support for ForeignKey field allowing to pass refrenced model.


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

- Support for [NullableObjectId](./fields.md#nullableobjectid) allowing special object ids to
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

- [exists()](./queries.md#exists) allowing to query for a document existance in the database.

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
- [Registry document checks](./registry.md#run-some-document-checks) allowing to check beforehand all the
index changes in a document.
- [Model check indexes](./documents.md#document-checks) to do the same checks for the indexes but for each document.
- [create_indexes_for_multiple_databases](./documents.md#create-indexes-for-multiple-databases).
- [drop_indexes_for_multiple_databases](./documents.md#drop-indexes-for-multiple-databases).

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
