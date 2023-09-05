from typing import TYPE_CHECKING, Any

from mongoz.core.db.querysets.base import QuerySet

if TYPE_CHECKING:
    pass


class Manager:
    """
    Base Manager for the Mongoz Models.
    To create a custom manager, the best approach is to inherit from the ModelManager.

    Example:
        from mongoz.managers import ModelManager
        from mongoz.models import Document


        class MyCustomManager(ModelManager):
            ...


        class MyOtherManager(ModelManager):
            ...


        class MyModel(mongoz.Document):
            query = MyCustomManager()
            active = MyOtherManager()

            ...
    """

    def __init__(self, model_class: Any = None):
        self.model_class = model_class

    def get_queryset(self) -> "QuerySet":
        """
        Returns the queryset object.

        Checks for a global possible tenant and returns the corresponding queryset.
        """
        return QuerySet(self.model_class)

    def __getattr__(self, item: Any) -> Any:
        """
        Gets the attribute from the queryset and if it does not
        exist, then lookup in the model.
        """
        try:
            return getattr(self.get_queryset(), item)
        except AttributeError:
            return getattr(self.model_class, item)
