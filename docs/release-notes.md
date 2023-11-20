# Release Notes

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
