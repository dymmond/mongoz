from typing import AsyncGenerator, List, Optional

import pydantic
import pytest
from tests.conftest import client

import mongoz
from mongoz import Document, Index, IndexType, ObjectId, Order

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
    uuid: Optional[ObjectId] = mongoz.ObjectId(null=True)
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
    await Movie.query().delete()
    await Movie.create_indexes()
    yield
    await Movie.drop_indexes(force=True)
    await Movie.query().delete()
    await Movie.create_indexes()


async def test_model_only() -> None:
    movies = await Movie.query().all()
    assert len(movies) == 0

    await Movie(
        name="Forrest Gump", year=2003, is_published=True, tags=["movie", "hollywood"]
    ).create()
    movies = await Movie.query().only("name", "tags").all()
    assert len(movies) == 1


async def test_model_only_attribute_error():
    barbie = await Movie(name="Barbie", year=2023, tags=["movie", "hollywood"]).create()
    movies = await Movie.query().only("name", "tags").all()

    assert len(movies) == 1
    assert movies[0].id == barbie.id

    with pytest.raises(AttributeError):
        movies[0].year  # noqa


async def test_model_only_with_all():
    await User(name="John", language="PT").create()
    await User(name="Jane", language="EN", description="Another simple description").create()

    users = await User.query().only("name", "language").all()

    assert len(users) == 2


async def test_model_only_with_filter():
    john = await User(name="John", language="PT").create()
    jane = await User(
        name="Jane", language="EN", description="Another simple description"
    ).create()

    users = await User.query(User.id == john.id).only("name", "language").all()

    assert len(users) == 1

    users = await User.query(User.id == jane.id).only("name", "language").all()

    assert len(users) == 1

    users = await User.query(User.id == 3).only("name", "language").all()

    assert len(users) == 0


async def test_model_only_save():
    user = await User(name="John", language="PT").create()

    user = await User.query(User.id == user.id).only("name", "language").get()
    user.name = "Edgy"
    user.language = "EN"
    user.description = "LOL"
    await user.save()

    user = await User.query(User.id == user.id).get()

    assert user.name == "Edgy"
    assert user.language == "EN"


async def test_model_only_save_without_nullable_field():
    user = await User(name="John", language="PT", description="John").create()

    assert user.description == "John"
    assert user.language == "PT"

    user = await User.query(User.id == user.id).only("description", "language").get()
    user.language = "EN"
    user.description = "A new description"
    await user.save()

    user = await User.query(User.id == user.id).get()

    assert user.name == "John"
    assert user.language == "EN"
    assert user.description == "A new description"


async def test_model_only_model_dump():
    user = await User(name="John", language="PT", description="A description").create()
    user = await User.query(User.id == user.id).only("name", "language").get()

    data = user.model_dump()

    assert "description" not in data
    assert data["id"] == user.id
    assert data["name"] == user.name
    assert data["language"] == user.language
