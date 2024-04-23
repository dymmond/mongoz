from typing import AsyncGenerator

import pydantic
import pytest

import mongoz
from mongoz.exceptions import FieldDefinitionError
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class User(mongoz.Document):
    name: str = mongoz.String(max_length=100)
    language: str = mongoz.String(max_length=200, null=True)
    description: str = mongoz.String(max_length=5000, null=True)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await User.objects.delete()
    yield
    await User.objects.delete()


@pytest.mark.parametrize(
    "value", [1, {"name": 1}, (1,), {"edgy"}], ids=["as-int", "as-dict", "as-tuple", "as-set"]
)
async def test_raise_exception(value):
    with pytest.raises(FieldDefinitionError):
        await User.objects.values(value)


async def test_model_values():
    user_1 = await User.objects.create(
        name="John", language="PT", description="A simple description"
    )
    user_2 = await User.objects.create(
        name="Jane", language="EN", description="Another simple description"
    )

    users = await User.objects.values()

    assert len(users) == 2

    assert users == [
        {"id": user_1.id, "name": "John", "language": "PT", "description": "A simple description"},
        {
            "id": user_2.id,
            "name": "Jane",
            "language": "EN",
            "description": "Another simple description",
        },
    ]


async def test_model_values_only_with_only():
    user_1 = await User.objects.create(name="John", language="PT")
    user_2 = await User.objects.create(
        name="Jane", language="EN", description="Another simple description"
    )

    users = await User.objects.only("name", "language").values()

    assert len(users) == 2

    assert users == [
        {"id": user_1.id, "name": "John", "language": "PT"},
        {"id": user_2.id, "name": "Jane", "language": "EN"},
    ]


async def test_model_values_list_fields():
    await User.objects.create(name="John", language="PT")
    await User.objects.create(name="Jane", language="EN", description="Another simple description")

    users = await User.objects.values(["name"])

    assert len(users) == 2

    assert users == [{"name": "John"}, {"name": "Jane"}]


async def test_model_values_exclude_fields():
    await User.objects.create(name="John", language="PT")
    await User.objects.create(name="Jane", language="EN", description="Another simple description")

    users = await User.objects.values(exclude=["name", "id"])
    assert len(users) == 2

    assert users == [
        {"language": "PT", "description": None},
        {"language": "EN", "description": "Another simple description"},
    ]


async def test_model_values_exclude_and_include_fields():
    user_1 = await User.objects.create(name="John", language="PT")
    user_2 = await User.objects.create(
        name="Jane", language="EN", description="Another simple description"
    )

    users = await User.objects.values(["id"], exclude=["name"])
    assert len(users) == 2

    assert users == [{"id": user_1.id}, {"id": user_2.id}]


async def test_model_values_exclude_none():
    user_1 = await User.objects.create(name="John", language="PT")
    user_2 = await User.objects.create(
        name="Jane", language="EN", description="Another simple description"
    )

    users = await User.objects.values(exclude_none=True)
    assert len(users) == 2

    assert users == [
        {"id": user_1.id, "name": "John", "language": "PT"},
        {
            "id": user_2.id,
            "name": "Jane",
            "language": "EN",
            "description": "Another simple description",
        },
    ]


async def test_model_only_with_filter():
    await User.objects.create(name="John", language="PT")
    user_2 = await User.objects.create(
        name="Jane", language="EN", description="Another simple description"
    )

    users = await User.objects.filter(id=user_2.id).values(["name"])
    assert len(users) == 1

    assert users == [{"name": "Jane"}]

    users = await User.objects.filter(id=3).values(["name"])

    assert len(users) == 0

    assert users == []
