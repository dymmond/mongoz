import typing

if typing.TYPE_CHECKING:
    from mongoz.core.db.documents import Document

# Create a var type for the Edgy Model
MongozDocument = typing.TypeVar("MongozDocument", bound="Document")


class AwaitableQuery(typing.Generic[MongozDocument]):
    __slots__ = ("model_class",)

    def __init__(self, model_class: typing.Type[MongozDocument]) -> None:
        self.model_class: typing.Type[MongozDocument] = model_class

    async def execute(self) -> typing.Any:
        raise NotImplementedError()
