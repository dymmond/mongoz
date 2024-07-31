from typing import List, Optional, AsyncGenerator

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


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.objects.using("test_my_db").delete()
    yield
    await Movie.objects.using("test_my_db").delete()


async def test_model_using_create() -> None:
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


async def test_model_using_update() -> None:
    await Movie.objects.using("test_my_db").create(name="Harshali", year=2024)

    movie = await Movie.objects.using("test_my_db").get()
    assert movie.name == "Harshali"

    await movie.update(name="Harshali Zode")

    movie = await Movie.objects.using("test_my_db").get()
    assert movie.name == "Harshali Zode"

    movie = await Movie.objects.using("test_my_db").filter(_id=movie.id).get()
    assert movie.name == "Harshali Zode"

    with pytest.raises(DocumentNotFound):
        await Movie.objects.filter(name="Harshali Zode").get()
        await Movie.objects.using("test_my_db").filter(name="Harshali").get()


async def test_model_delete() -> None:
    await Movie.objects.using("test_my_db").create(name="Harshali Zode", year=2024)

    movie = await Movie.objects.using("test_my_db").get()
    assert movie.name == "Harshali Zode"

    await movie.delete()

    with pytest.raises(DocumentNotFound):
        movie = await Movie.objects.using("test_my_db").get()


async def test_model_save() -> None:
    await Movie.objects.using("test_my_db").create(name="Harshali", year=2024)

    movie = await Movie.objects.using("test_my_db").get()
    assert movie.name == "Harshali"

    movie.name = "Harshali Zode"
    await movie.save()

    movie = await Movie.objects.using("test_my_db").get()
    assert movie.name == "Harshali Zode"

    movie = await Movie.objects.using("test_my_db").filter(_id=movie.id).get()
    assert movie.name == "Harshali Zode"

    with pytest.raises(DocumentNotFound):
        await Movie.objects.filter(name="Harshali Zode").get()
        await Movie.objects.using("test_my_db").filter(name="Harshali").get()
