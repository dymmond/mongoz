from typing import TYPE_CHECKING, Type, cast

from mongoz.core.connection.registry import Registry

if TYPE_CHECKING:
    from mongoz.core.db.documents.document import Document


def get_model(registry: Registry, model_name: str) -> Type["Document"]:
    """
    Return the model with capitalize model_name.

    Raise lookup error if no model is found.
    """
    try:
        return cast("Type[Document]", registry.models[model_name])
    except KeyError:
        raise LookupError(f"Registry doesn't have a {model_name} document.") from None
