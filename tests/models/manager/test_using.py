from typing import List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, ObjectId
from mongoz.exceptions import DocumentNotFound
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)

    class Meta:
        registry = client
        database = "test_db"


async def test_model_using() -> None:
    await Movie.objects.create(name="Harshali", year=2024)
    await Movie.objects.using("test_my_db").create(name="Harshali Zode", year=2024)

    movie = await Movie.objects.get()
    assert movie.name == "Harshali"

    movie = await Movie.objects.using("test_my_db").get()
    assert movie.name == "Harshali Zode"

    movie = await Movie.objects.using("test_my_db").filter(name="Harshali Zode").get()
    assert movie.name == "Harshali Zode"

    movie = await Movie.objects.using("test_my_db").filter(_id=movie.id).get()
    assert movie.name == "Harshali Zode"

    with pytest.raises(DocumentNotFound):
        await Movie.objects.filter(name="Harshali Zode").get()
        await Movie.objects.using("test_my_db").filter(name="Harshali").get()
