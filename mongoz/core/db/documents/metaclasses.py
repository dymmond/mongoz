import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
    no_type_check,
)

from pydantic._internal._model_construction import ModelMetaclass

from mongoz.core.connection.collections import Collection
from mongoz.core.connection.registry import Registry
from mongoz.core.db.datastructures import Index
from mongoz.core.db.documents.managers import Manager
from mongoz.core.db.fields.core import BaseField
from mongoz.core.utils.functional import extract_field_annotations_and_defaults, mongoz_setattr
from mongoz.exceptions import ImproperlyConfigured

if TYPE_CHECKING:
    from mongoz.core.db.documents import Document


class MetaInfo:
    __slots__ = (
        "pk",
        "pk_attribute",
        "abstract",
        "fields",
        "fields_mapping",
        "registry",
        "collection",
        "indexes",
        "parents",
        "manager",
        "model",
        "managers",
        "signals",
    )

    def __init__(self, meta: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.pk: Optional[BaseField] = None
        self.pk_attribute: Union[BaseField, str] = getattr(meta, "pk_attribute", "")
        self.abstract: bool = getattr(meta, "abstract", False)
        self.fields: Set[Any] = set()
        self.fields_mapping: Dict[str, BaseField] = {}
        self.registry: Optional[Type[Registry]] = getattr(meta, "registry", None)
        self.collection: Optional[Collection] = getattr(meta, "collection", None)
        self.parents: Any = getattr(meta, "parents", None) or []
        self.model: Optional[Type["Document"]] = None
        self.manager: "Manager" = getattr(meta, "manager", Manager())
        self.indexes: List[Index] = getattr(meta, "indexes", None)
        self.managers: List[Manager] = getattr(meta, "managers", [])
        # self.signals: Optional[Broadcaster] = {}  # type: ignore

    def model_dump(self) -> Dict[Any, Any]:
        return {k: getattr(self, k, None) for k in self.__slots__}

    def load_dict(self, values: Dict[str, Any]) -> None:
        """
        Loads the metadata from a dictionary
        """
        for key, value in values.items():
            mongoz_setattr(self, key, value)


def _check_model_inherited_registry(bases: Tuple[Type, ...]) -> Type[Registry]:
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
            "Registry for the table not found in the Meta class or any of the superclasses. You must set thr registry in the Meta."
        )
    return found_registry


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


class BaseModelMeta(ModelMetaclass):
    __mongoz_fields__: ClassVar[Mapping[str, Type["BaseField"]]]

    @no_type_check
    def __new__(cls, name: str, bases: Tuple[Type, ...], attrs: Any) -> Any:
        fields: Dict[str, BaseField] = {}
        meta_class: "object" = attrs.get("Meta", type("Meta", (), {}))
        pk_attribute: str = "id"
        registry: Any = None

        # Extract the custom Mongoz Fields in a pydantic format.
        attrs, model_fields = extract_field_annotations_and_defaults(attrs)
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

                _check_manager_for_bases(base, attrs)  # type: ignore
            else:
                # abstract classes
                for key, value in meta.fields_mapping.items():
                    attrs[key] = value

                # For managers coming from the top that are not abstract classes
                _check_manager_for_bases(base, attrs, meta)  # type: ignore

        # Search in the base classes
        inherited_fields: Any = {}
        for base in bases:
            __search_for_fields(base, inherited_fields)

        if inherited_fields:
            # Making sure the inherited fields are before the new defined.
            attrs = {**inherited_fields, **attrs}

        for key, value in attrs.items():
            if isinstance(value, BaseField):
                if (
                    getattr(meta_class, "abstract", None) is None
                    or getattr(meta_class, "abstract", False) is False
                ):
                    fields[key] = value

        for slot in fields:
            attrs.pop(slot, None)

        attrs["meta"] = meta = MetaInfo(meta_class)

        meta.fields_mapping = fields
        meta.pk_attribute = pk_attribute
        meta.pk = fields.get(pk_attribute)

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
            if getattr(meta, "indexes", None) is not None:
                raise ImproperlyConfigured("indexes cannot be in abstract classes.")
        else:
            meta.managers = [k for k, v in attrs.items() if isinstance(v, Manager)]

        # Handle the registry of models
        if getattr(meta, "registry", None) is None:
            if (
                hasattr(new_class, "__db_model__")
                and new_class.__db_model__
                and hasattr(new_class, "__embedded__")
                and new_class.__embedded__
            ):
                meta.registry = _check_model_inherited_registry(bases)
            else:
                return new_class

        # Making sure the collection is always set if the value is not provided
        if getattr(meta, "collection", None) is None:
            collection = f"{name.lower()}s"
            meta.collection = collection

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

        for _, field in meta.fields_mapping.items():
            field.registry = registry

        new_class.__db_model__ = True
        cls.__mongoz_fields__ = meta.fields_mapping
        meta.model = new_class
        meta.manager.model_class = new_class

        # Set the owner of the field
        for _, value in new_class.__mongoz_fields__.items():
            value.owner = new_class

        # Set the manager
        for _, value in attrs.items():
            if isinstance(value, Manager):
                value.model_class = new_class

        # Update the model references with the validations of the model
        # Being done by the Mongoz fields instead.
        # Generates a proxy model for each model created
        # Making sure the core model where the fields are inherited
        # And mapped contains the main proxy_model
        if not new_class.is_proxy_model and not new_class.meta.abstract:
            proxy_model = new_class.generate_proxy_model()
            new_class.__proxy_model__ = proxy_model
            new_class.__proxy_model__.parent = new_class
            new_class.__proxy_model__.model_rebuild(force=True)

        new_class.model_rebuild(force=True)
        return new_class

    @property
    def proxy_model(cls) -> Any:
        """
        Returns the proxy_model from the Document when called using the cache.
        """
        return cls.__proxy_model__


class EmbeddedModelMetaClass(ModelMetaclass):
    __mongoz_fields__: Mapping[str, BaseField]

    @no_type_check
    def __new__(cls, name: str, bases: Tuple[Type, ...], attrs: Any) -> Any:
        # Extract the custom Mongoz Fields in a pydantic format.
        attrs, model_fields = extract_field_annotations_and_defaults(attrs)
        cls = super().__new__(cls, name, bases, attrs)
        cls.__mongoz_fields__ = model_fields
        return cls
