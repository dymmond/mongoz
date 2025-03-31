from typing import AsyncGenerator, List, Optional

import pydantic
import pytest

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]

indexes = [
    Index("name", unique=True),
    Index(keys=[("year", Order.DESCENDING), ("genre", IndexType.HASHED)]),
]


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)
    uuid: Optional[ObjectId] = mongoz.UUID(null=True)
    is_published: bool = mongoz.Boolean(default=False)

    class Meta:
        registry = client
        database = "test_db"
        indexes = indexes


class User(mongoz.Document):
    name: str = mongoz.String(max_length=100)
    language: str = mongoz.String(max_length=200, null=True)
    description: str = mongoz.String(max_length=5000, null=True)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()
    await Movie.create_indexes()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.objects.delete()
    await Movie.create_indexes()


async def test_model_defer() -> None:
    movies = await Movie.objects.all()
    assert len(movies) == 0

    await Movie.objects.create(
        name="Forrest Gump",
        year=2003,
        is_published=True,
        tags=["movie", "hollywood"],
    )
    movies = await Movie.objects.defer("name", "tags")
    assert len(movies) == 1


@pytest.mark.parametrize("field", ["name", "tags"])
async def test_model_defer_attribute_error(field):
    barbie = await Movie.objects.create(
        name="Barbie", year=2023, tags=["movie", "hollywood"]
    )
    movies = await Movie.objects.defer("name", "tags")

    assert len(movies) == 1
    assert movies[0].id == barbie.id

    with pytest.raises(AttributeError):
        getattr(movies[0], field)  # noqa


async def test_model_defer_with_all():
    await User.objects.create(name="John", language="PT")
    await User.objects.create(
        name="Jane", language="EN", description="Another simple description"
    )

    users = await User.objects.defer("name", "language").all()

    assert len(users) == 2


async def test_model_defer_with_filter():
    john = await User.objects.create(name="John", language="PT")
    jane = await User.objects.create(
        name="Jane", language="EN", description="Another simple description"
    )

    users = await User.objects.filter(pk=john.id).defer("name", "language")

    assert len(users) == 1

    user = users[0]

    assert user.model_dump() == {"id": john.id, "description": None}

    users = await User.objects.filter(id=jane.id).defer("name", "language")

    assert len(users) == 1

    users = await User.objects.filter(id=3).defer("name", "language")

    assert len(users) == 0


async def test_model_defer_save():
    user = await User.objects.create(name="John", language="PT")

    user = (
        await User.objects.filter(pk=user.id).defer("name", "language").get()
    )
    user.name = "Edgy"
    user.language = "EN"
    user.description = "LOL"

    await user.save()

    user = await User.objects.get(pk=user.id)

    assert user.name == "Edgy"
    assert user.language == "EN"


async def test_model_defer_save_without_nullable_field():
    user = await User.objects.create(
        name="John", language="PT", description="John"
    )

    assert user.description == "John"
    assert user.language == "PT"

    user = (
        await User.objects.filter(pk=user.id)
        .defer("description", "language")
        .get()
    )
    user.language = "EN"
    user.description = "A new description"
    await user.save()

    user = await User.objects.get(pk=user.id)

    assert user.name == "John"
    assert user.language == "EN"
    assert user.description == "A new description"


async def test_model_defer_model_dump():
    user = await User.objects.create(
        name="John", language="PT", description="A description"
    )
    user = (
        await User.objects.filter(pk=user.id).defer("name", "language").get()
    )

    data = user.model_dump()

    assert data["description"] == user.description
    assert "name" not in data
    assert "language" not in data
