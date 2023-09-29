from typing import List

from mongoz import MongozSettings


class MyCustomSettings(MongozSettings):
    """
    My settings overriding default values and add new ones.
    """

    parsed_ids: List[str] = ["id", "pk"]
