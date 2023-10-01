import typing


class MongozException(Exception):
    def __init__(
        self,
        *args: typing.Any,
        detail: str = "",
    ):
        self.detail = detail
        super().__init__(*(str(arg) for arg in args if arg), self.detail)

    def __repr__(self) -> str:
        if self.detail:
            return f"{self.__class__.__name__} - {self.detail}"
        return self.__class__.__name__

    def __str__(self) -> str:
        return "".join(self.args).strip()


class DocumentNotFound(MongozException):
    ...


class MultipleDocumentsReturned(MongozException):
    ...


class FieldDefinitionError(MongozException):
    ...


class ImproperlyConfigured(MongozException):
    ...


class InvalidObjectIdError(MongozException):
    ...


class InvalidKeyError(MongozException):
    ...


class SignalError(MongozException):
    ...


class AbstractDocumentError(MongozException):
    ...


class OperatorInvalid(MongozException):
    ...


class IndexError(MongozException):
    ...
