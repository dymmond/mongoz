import json
import warnings

import bson
import pytest
from pydantic.warnings import PydanticDeprecationWarning
from pydantic_core import PydanticSerializationError

from mongoz.core.db.documents._internal import ModelDump
from mongoz.core.db.documents.base import MongozBaseModel
from mongoz.core.signals import Signal

pytestmark = pytest.mark.anyio


async def test_model_construction_and_json_serialization_use_supported_pydantic_apis() -> None:
    object_id = bson.ObjectId()

    with warnings.catch_warnings():
        warnings.simplefilter("error", PydanticDeprecationWarning)

        class Unsupported:
            pass

        class Payload(MongozBaseModel):
            pass

        class SerializedPayload(ModelDump):
            object_ids: list[bson.ObjectId]
            collections: dict[str, object]
            signal: Signal

        class UnsupportedPayload(ModelDump):
            value: Unsupported

        payload = Payload()
        serialized = SerializedPayload(
            object_ids=[object_id],
            collections={
                "tuple": (object_id,),
                "set": {object_id},
                "frozenset": frozenset({object_id}),
                "plain": "unchanged",
            },
            signal=Signal(),
        )
        unsupported = UnsupportedPayload(value=Unsupported())

        assert payload.model_dump() == {"id": None}
        assert serialized.model_dump(mode="json")["object_ids"] == [str(object_id)]
        serialized_json = json.loads(serialized.model_dump_json())
        assert serialized_json["object_ids"] == [str(object_id)]
        assert serialized_json["collections"] == {
            "tuple": [str(object_id)],
            "set": [str(object_id)],
            "frozenset": [str(object_id)],
            "plain": "unchanged",
        }
        assert isinstance(serialized_json["signal"], str)
        with pytest.raises(PydanticSerializationError, match="Unable to serialize unknown type"):
            unsupported.model_dump_json()
