import json
import warnings
from datetime import datetime, timezone

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
                "mixed": [object_id, datetime(2026, 1, 2, tzinfo=timezone.utc)],
            },
            signal=Signal(),
            extra_object_id=object_id,
            extra_mixed=[object_id, datetime(2026, 1, 3, tzinfo=timezone.utc)],
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
            "mixed": [str(object_id), "2026-01-02T00:00:00Z"],
        }
        assert isinstance(serialized_json["signal"], str)
        assert serialized_json["extra_object_id"] == str(object_id)
        assert serialized_json["extra_mixed"] == [str(object_id), "2026-01-03T00:00:00Z"]
        with pytest.raises(PydanticSerializationError, match="Unable to serialize unknown type"):
            unsupported.model_dump_json()

        unsupported_extra = ModelDump(extra_value=Unsupported())
        with pytest.raises(PydanticSerializationError, match="Unable to serialize unknown type"):
            unsupported_extra.model_dump_json()
