from typing import Any, Type, cast

from mongoz.core.db.querysets.core.manager import Manager as BaseManager


class QuerySetManager:

    def __init__(self, model_class: Any = None):
        self.model_class = model_class

    def __get__(self, _: Any, owner: Any) -> Type["BaseManager"]:
        return cast("Type[BaseManager]", self.__class__(model_class=owner))

    def get_queryset(self) -> "BaseManager":
        """
        Returns the queryset object.

        Checks for a global possible tenant and returns the corresponding queryset.
        """
        return BaseManager(self.model_class)

    def __getattr__(self, item: Any) -> Any:
        """
        Gets the attribute from the queryset and if it does not
        exist, then lookup in the model.
        """
        try:
            return getattr(self.get_queryset(), item)
        except AttributeError:
            return getattr(self.model_class, item)
