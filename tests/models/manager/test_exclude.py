from typing import AsyncGenerator

import pydantic
import pytest
from tests.conftest import client

import mongoz
from mongoz import Index, IndexType, Order

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]

indexes = [
    Index("name", unique=True),
    Index(keys=[("year", Order.DESCENDING), ("genre", IndexType.HASHED)]),
]


class User(mongoz.Document):
    name: str = mongoz.String(max_length=100)
    language: str = mongoz.String(max_length=200, null=True)
    description: str = mongoz.String(max_length=5000, null=True)
    is_active: bool = mongoz.Boolean(default=True)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await User.objects.delete()
    yield
    await User.objects.delete()


async def test_model_exclude() -> None:
    user1 = await User.objects.create(name="Mongoz")
    await User.objects.create(name="Edgy", is_active=False)

    users = await User.objects.exclude(is_active=False)
    assert len(users) == 1

    assert users[0].id == user1.id


async def test_model_exclude_operators() -> None:
    user1 = await User.objects.create(name="Mongoz", language="EN")
    user2 = await User.objects.create(name="Edgy", language="PT", is_active=False)
    user3 = await User.objects.create(name="Saffier", language="EN")

    users = await User.objects.exclude(language__in=["EN"])
    assert len(users) == 1

    assert users[0].id == user2.id

    users = await User.objects.exclude(id=user1.id)
    assert len(users) == 2
    assert users[0].id == user2.id
    assert users[1].id == user3.id

    users = await User.objects.exclude(language__not_in=["EN"])
    assert len(users) == 2
    assert users[0].id == user1.id
    assert users[1].id == user3.id

    users = await User.objects.exclude(language__asc=True)
    assert len(users) == 3


async def test_model_exclude_with_filter() -> None:
    await User.objects.create(name="Mongoz")
    user2 = await User.objects.create(name="Edgy", is_active=False)

    users = await User.objects.filter(is_active=False).exclude(is_active=True)
    assert len(users) == 1

    assert users[0].id == user2.id
