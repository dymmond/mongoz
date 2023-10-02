from typing import TYPE_CHECKING, Any, Dict, Optional, Set, Tuple, Type, Union

from pydantic import ConfigDict

import mongoz

if TYPE_CHECKING:
    from mongoz import Document
    from mongoz.core.db.documents.metaclasses import MetaInfo

edgy_setattr = object.__setattr__


def create_mongoz_document(
    __name__: str,
    __module__: str,
    __definitions__: Optional[Dict[Any, Any]] = None,
    __metadata__: Optional[Type["MetaInfo"]] = None,
    __qualname__: Optional[str] = None,
    __config__: Optional[ConfigDict] = None,
    __bases__: Optional[Tuple[Type["Document"]]] = None,
    __proxy__: bool = False,
    __pydantic_extra__: Any = None,
) -> Type["Document"]:
    """
    Generates an `mongoz.Document` with all the required definitions to generate the pydantic
    like model.
    """
    if not __bases__:
        __bases__ = (mongoz.Document,)

    qualname = __qualname__ or __name__
    core_definitions = {
        "__module__": __module__,
        "__qualname__": qualname,
        "is_proxy_document": __proxy__,
    }
    if not __definitions__:
        __definitions__ = {}

    core_definitions.update(**__definitions__)

    if __config__:
        core_definitions.update(**{"model_config": __config__})
    if __metadata__:
        core_definitions.update(**{"Meta": __metadata__})
    if __pydantic_extra__:
        core_definitions.update(**{"__pydantic_extra__": __pydantic_extra__})

    model: Type["Document"] = type(__name__, __bases__, core_definitions)
    return model


def generify_model_fields(
    model: Type["Document"], exclude: Union[Set[str], None] = None
) -> Dict[Any, Any]:
    """
    Makes all fields generic when a partial model is generated or used.
    This also removes any metadata for the field such as validations making
    it a clean slate to be used internally to process dynamic data and removing
    the constraints of the original model fields.
    """
    fields = {}

    if exclude is None:
        exclude = set()

    # handle the nested non existing results
    for name, field in model.model_fields.items():
        if name in exclude:
            continue

        edgy_setattr(field, "annotation", Any)
        edgy_setattr(field, "null", True)
        edgy_setattr(field, "metadata", [])
        fields[name] = field
    return fields
