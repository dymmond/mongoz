from typing import TYPE_CHECKING, Any, Dict, Tuple, Type, Union, cast

from pydantic import ConfigDict

if TYPE_CHECKING:
    from mongoz import Document
    from mongoz.core.db.documents.metaclasses import MetaInfo


class ProxyDocument:
    """
    When a model needs to be mirrored without affecting the
    original, this instance is triggered instead.
    """

    def __init__(
        self,
        name: str,
        module: str,
        *,
        bases: Union[Tuple[Type["Document"]], None] = None,
        definitions: Union[Dict[Any, Any], None] = None,
        metadata: Union[Type["MetaInfo"], None] = None,
        qualname: Union[str, None] = None,
        config: Union[ConfigDict, None] = None,
        proxy: bool = True,
        pydantic_extra: Union[Any, None] = None,
    ) -> None:
        self.__name__: str = name
        self.__module__: str = module
        self.__bases__: Union[Tuple[Type["Document"]], None] = bases
        self.__definitions__: Union[Dict[Any, Any], None] = definitions
        self.__metadata__: Union[Type["MetaInfo"], None] = metadata
        self.__qualname__: Union[str, None] = qualname
        self.__config__: Union[ConfigDict, None] = config
        self.__proxy__: bool = proxy
        self.__pydantic_extra__ = pydantic_extra
        self.__model__ = None

    def build(self) -> "ProxyDocument":
        """
        Generates the model proxy for the __model__ definition.
        """
        from mongoz.core.utils.documents import create_mongoz_document

        model: Type["Document"] = create_mongoz_document(
            __name__=self.__name__,
            __module__=self.__module__,
            __bases__=self.__bases__,
            __definitions__=self.__definitions__,
            __metadata__=self.__metadata__,
            __qualname__=self.__qualname__,
            __config__=self.__config__,
            __proxy__=self.__proxy__,
            __pydantic_extra__=self.__pydantic_extra__,
        )
        self.__model__ = model  # type: ignore
        return self

    @property
    def model(self) -> Type["Document"]:
        return cast("Type[Document]", self.__model__)

    @model.setter
    def model(self, value: Type["Document"]) -> None:
        self.__model__ = value  # type: ignore

    def __repr__(self) -> str:
        name = f"Proxy{self.__name__}"
        return f"<{name}: [{self.__definitions__}]"
