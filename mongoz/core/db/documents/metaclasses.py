import copy
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
    no_type_check,
)

from pydantic._internal._model_construction import ModelMetaclass

from mongoz.core.connection.collections import Collection
from mongoz.core.connection.database import Database
from mongoz.core.connection.registry import Registry
from mongoz.core.db.datastructures import Index
from mongoz.core.db.fields.base import BaseField, MongozField
from mongoz.core.db.querysets.core.manager import Manager
from mongoz.core.signals import Broadcaster, Signal
from mongoz.core.utils.functional import extract_field_annotations_and_defaults, mongoz_setattr
from mongoz.core.utils.sync import run_sync
from mongoz.exceptions import ImproperlyConfigured, IndexError

if TYPE_CHECKING:
    from mongoz.core.db.documents import Document
    from mongoz.core.db.documents.document_proxy import ProxyDocument


class MetaInfo:
    __slots__ = (
        "pk",
        "id_attribute",
        "abstract",
        "fields",
        "registry",
        "collection",
        "indexes",
        "parents",
        "signals",
        "database",
        "manager",
        "autogenerate_index",
    )

    def __init__(self, meta: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.pk: Optional[BaseField] = None
        self.id_attribute: Union[BaseField, str] = getattr(meta, "id_attribute", "")
        self.abstract: bool = getattr(meta, "abstract", False)
        self.fields: Dict[str, BaseField] = {}
        self.registry: Optional[Type[Registry]] = getattr(meta, "registry", None)
        self.collection: Optional[Collection] = getattr(meta, "collection", None)
        self.parents: Any = getattr(meta, "parents", None) or []
        self.indexes: List[Index] = cast(List[Index], getattr(meta, "indexes", None))
        self.database: Union["str", Database] = cast(
            Union["str", Database], getattr(meta, "database", None)
        )
        self.signals: Optional[Broadcaster] = {}  # type: ignore
        self.manager: "Manager" = getattr(meta, "manager", Manager())
        self.autogenerate_index: bool = getattr(meta, "autogenerate_index", False)

    def model_dump(self) -> Dict[Any, Any]:
        return {k: getattr(self, k, None) for k in self.__slots__}

    def load_dict(self, values: Dict[str, Any]) -> None:
        """
        Loads the metadata from a dictionary
        """
        for key, value in values.items():
            mongoz_setattr(self, key, value)


def _check_manager_for_bases(
    base: Tuple[Type, ...],
    attrs: Any,
    meta: Optional[MetaInfo] = None,
) -> None:
    """
    When an abstract class is declared, we must treat the manager's value coming from the top.
    """
    if not meta:
        for key, value in inspect.getmembers(base):
            if isinstance(value, Manager) and key not in attrs:
                attrs[key] = value.__class__()
    else:
        if not meta.abstract:
            for key, value in inspect.getmembers(base):
                if isinstance(value, Manager) and key not in attrs:
                    attrs[key] = value.__class__()


def _check_document_inherited_registry(bases: Tuple[Type, ...]) -> Type[Registry]:
    """
    When a registry is missing from the Meta class, it should look up for the bases
    and obtain the first found registry.

    If not found, then a ImproperlyConfigured exception is raised.
    """
    found_registry: Optional[Type[Registry]] = None
    for base in bases:
        meta: MetaInfo = getattr(base, "meta", None)  # type: ignore
        if not meta:
            continue

        if getattr(meta, "registry", None) is not None:
            found_registry = meta.registry
            break

    if not found_registry:
        raise ImproperlyConfigured(
            "Registry for the table not found in the Meta class or any of the superclasses. You must set the registry in the Meta."
        )
    return found_registry


def _check_document_inherited_indexes(bases: Tuple[Type, ...]) -> List[Any]:
    """
    Checks if there are any indexes from the inherited document.
    """
    found_indexes: List[Any] = []
    for base in bases:
        meta: MetaInfo = getattr(base, "meta", None)  # type: ignore
        if not meta:
            continue

        if getattr(meta, "indexes", None) is not None:
            found_indexes.extend(meta.indexes)
            break

    return found_indexes


def _check_document_inherited_database(
    bases: Tuple[Type, ...], registry: Registry
) -> Union[str, Database]:
    """
    When a database is missing from the Meta class, it should look up for the bases
    and obtain the first found database.

    If not found, then a ImproperlyConfigured exception is raised.
    """
    found_database: Union[str, Database, None] = None

    for base in bases:
        meta: MetaInfo = getattr(base, "meta", None)  # type: ignore
        if not meta:
            continue

        if getattr(meta, "database", None) is not None:
            if isinstance(meta.database, str):
                found_database = registry.get_database(meta.database)
                break
            elif isinstance(meta.database, Database):
                found_database = meta.database
                break
            raise ImproperlyConfigured(
                "database must be a string name or an instance of mongoz.Database."
            )

    if not found_database:
        raise ImproperlyConfigured(
            "'database' for the table not found in the Meta class or any of the superclasses. You must set the database in the Meta."
        )
    return found_database


def _register_document_signals(model_class: Type["Document"]) -> None:
    """
    Registers the signals in the model's Broadcaster and sets the defaults.
    """
    signals = Broadcaster()
    signals.pre_save = Signal()
    signals.pre_update = Signal()
    signals.pre_delete = Signal()
    signals.post_save = Signal()
    signals.post_update = Signal()
    signals.post_delete = Signal()
    model_class.meta.signals = signals


class BaseModelMeta(ModelMetaclass):
    __mongoz_fields__: ClassVar[Mapping[str, Type["MongozField"]]] = {}

    @no_type_check
    def __new__(cls, name: str, bases: Tuple[Type, ...], attrs: Any) -> Any:
        fields: Dict[str, BaseField] = {}
        meta_class: "object" = attrs.get("Meta", type("Meta", (), {}))
        id_attribute: str = "id"
        id_attribute_alias: str = "_id"
        registry: Any = None

        # Extract the custom Mongoz Fields in a pydantic format.
        attrs, model_fields = extract_field_annotations_and_defaults(attrs)
        cls.__mongoz_fields__ = model_fields
        super().__new__(cls, name, bases, attrs)

        # Searching for fields "Field" in the class hierarchy.
        def __search_for_fields(base: Type, attrs: Any) -> None:
            """
            Search for class attributes of the type fields.Field in the given class.

            If a class attribute is an instance of the Field, then it will be added to the
            field_mapping but only if the key does not exist already.
            """
            for parent in base.__mro__[1:]:
                __search_for_fields(parent, attrs)

            meta: Union[MetaInfo, None] = getattr(base, "meta", None)
            if not meta:
                # Mixins and other classes
                for key, value in inspect.getmembers(base):
                    if isinstance(value, BaseField) and key not in attrs:
                        attrs[key] = value
                _check_manager_for_bases(base, attrs)
            else:
                # abstract classes
                for key, value in meta.fields.items():
                    attrs[key] = value
                _check_manager_for_bases(base, attrs)

        # Search in the base classes
        inherited_fields: Any = {}
        for base in bases:
            __search_for_fields(base, inherited_fields)

        if inherited_fields:
            # Making sure the inherited fields are before the new defined.
            attrs = {**inherited_fields, **attrs}

        for key, value in attrs.items():
            if isinstance(value, (BaseField)):
                if getattr(meta_class, "abstract", None):
                    value = copy.copy(value)
                fields[key] = value

        for slot in fields:
            attrs.pop(slot, None)

        attrs["meta"] = meta = MetaInfo(meta_class)
        meta.fields = fields
        meta.id_attribute = id_attribute
        meta.pk = fields.get(id_attribute)

        if not fields:
            meta.abstract = True

        model_class = super().__new__

        # Ensure the initialization is only performed for subclasses of Document
        parents = [parent for parent in bases if isinstance(parent, BaseModelMeta)]
        if not parents:
            return model_class(cls, name, bases, attrs)

        meta.parents = parents
        new_class = cast("Type[Document]", model_class(cls, name, bases, attrs))

        # Update the model_fields are updated to the latest
        new_class.model_fields.update(model_fields)

        # Abstract classes do not allow multiple managers. This make sure it is enforced.
        if meta.abstract:
            managers = [k for k, v in attrs.items() if isinstance(v, Manager)]
            if len(managers) > 1:
                raise ImproperlyConfigured(
                    "Multiple managers are not allowed in abstract classes."
                )

        if "id" in new_class.model_fields:
            new_class.model_fields["id"].default = None

        # Handle the registry of models
        if getattr(meta, "registry", None) is None:
            if hasattr(new_class, "__db_document__") and new_class.__db_document__:
                meta.registry = _check_document_inherited_registry(bases)
            else:
                return new_class

        # Making sure the collection is always set if the value is not provided
        collection_name: Optional[str] = None
        if getattr(meta, "collection", None) is None:
            collection_name = f"{name.lower()}s"
        else:
            collection_name = meta.collection.name

        # Assert the databse is also specified
        if getattr(meta, "database", None) is None:
            meta.database = _check_document_inherited_database(bases, registry=meta.registry)
        else:
            if isinstance(meta.database, str):
                meta.database = meta.registry.get_database(meta.database)
            elif not isinstance(meta.database, Database):
                raise ImproperlyConfigured(
                    "database must be a string name or an instance of mongoz.Database."
                )

        # Handle indexes
        if getattr(meta, "indexes", None) is not None:
            indexes = meta.indexes
            if not isinstance(indexes, (list, tuple)):
                value_type = type(indexes).__name__
                raise ImproperlyConfigured(
                    f"indexes must be a tuple or list. Got {value_type} instead."
                )
            else:
                if not all(isinstance(value, Index) for value in indexes):
                    raise ValueError("Meta.indexes must be a list of Index types.")

                # Extend existing indexes.
                indexes.extend(_check_document_inherited_indexes(bases))

        for _, field in meta.fields.items():
            field.registry = registry

        # Making sure it does not generate tables if abstract it set
        registry = meta.registry
        if not meta.abstract:
            registry.documents[name] = new_class

        new_class.__db_document__ = True
        meta.collection = meta.database.get_collection(collection_name)

        mongoz_fields: Dict[str, MongozField] = {}
        for field_name, field in new_class.model_fields.items():
            if not field.alias and field_name != id_attribute:
                field.alias = field_name
            elif field_name == id_attribute:
                field.alias = id_attribute_alias
            new_field = MongozField(pydantic_field=field, model_class=field.annotation)
            mongoz_fields[field_name] = new_field

        # For inherited fields
        # We need to make sure the default is the pydantic_field
        # and not the MongozField itself and create any index as well.

        for name, field in new_class.model_fields.items():
            if isinstance(field.default, MongozField):
                new_class.model_fields[name] = field.default.pydantic_field

            if not new_class.is_proxy_document:
                # For the indexes
                _index: Union[Index, None] = None
                if hasattr(field, "index") and field.index and field.unique:
                    _index = Index(name, unique=True, sparse=field.sparse)
                elif hasattr(field, "index") and field.index:
                    _index = Index(name, sparse=field.sparse)
                elif hasattr(field, "unique") and field.unique:
                    _index = Index(name, unique=True)

                if _index is not None:
                    index_names = [index.name for index in meta.indexes or []]
                    if _index.name in index_names:
                        raise IndexError(
                            f"There is already an index with the name `{_index.name}`"
                        )

                    if meta.indexes is None:
                        meta.indexes = []
                    meta.indexes.insert(0, _index)

        # Set the manager
        for _, value in attrs.items():
            if isinstance(value, Manager):
                value.model_class = new_class
                value._collection = new_class.meta.collection._collection

        # Register the signals
        _register_document_signals(new_class)

        new_class.Meta = meta
        new_class.__mongoz_fields__ = mongoz_fields

        # Update the model references with the validations of the model
        # Being done by the Edgy fields instead.
        # Generates a proxy model for each model created
        # Making sure the core model where the fields are inherited
        # And mapped contains the main proxy_document
        if not new_class.is_proxy_document and not new_class.meta.abstract:
            proxy_document: "ProxyDocument" = new_class.generate_proxy_document()
            new_class.__proxy_document__ = proxy_document
            new_class.__proxy_document__.parent = new_class
            new_class.__proxy_document__.model_rebuild(force=True)
            meta.registry.documents[new_class.__name__] = new_class

        new_class.model_rebuild(force=True)

        # Build the indexes
        if not meta.abstract and meta.indexes and meta.autogenerate_index:
            if not new_class.is_proxy_document:
                run_sync(new_class.create_indexes())
        return new_class

    @property
    def signals(cls) -> "Broadcaster":
        """
        Returns the signals of a class
        """
        return cast("Broadcaster", cls.meta.signals)

    @property
    def proxy_document(cls) -> Any:
        """
        Returns the proxy_document from the Document when called using the cache.
        """
        return cls.__proxy_document__

    def __getattr__(self, name: str) -> Any:
        if name in self.__mongoz_fields__:
            return self.__mongoz_fields__[name]
        return super().__getattribute__(name)


class EmbeddedModelMetaClass(ModelMetaclass):
    __mongoz_fields__: ClassVar[Mapping[str, Type["MongozField"]]]

    @no_type_check
    def __new__(cls, name: str, bases: Tuple[Type, ...], attrs: Any) -> Any:
        attrs, model_fields = extract_field_annotations_and_defaults(attrs)
        cls.__mongoz_fields__ = model_fields
        new_class = super().__new__(cls, name, bases, attrs)

        mongoz_fields: Dict[str, MongozField] = {}
        for field_name, field in new_class.model_fields.items():
            if not field.alias:
                field.alias = field_name
            new_field = MongozField(pydantic_field=field, model_class=new_class)
            mongoz_fields[field_name] = new_field

        new_class.__mongoz_fields__ = mongoz_fields
        return new_class
