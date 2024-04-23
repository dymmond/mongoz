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
    await User.query().delete()
    yield
    await User.query().delete()


async def test_model_values():
    user_1 = await User(name="John", language="PT", description="A simple description").create()
    user_2 = await User(
        name="Jane", language="EN", description="Another simple description"
    ).create()

    users = await User.query().values_list()

    assert len(users) == 2

    assert users == [
        (user_1.id, "John", "PT", "A simple description"),
        (user_2.id, "Jane", "EN", "Another simple description"),
    ]


async def test_model_values_only_with_only():
    john = await User(name="John", language="PT").create()
    jane = await User(
        name="Jane", language="EN", description="Another simple description"
    ).create()

    users = await User.query().only("name", "language").values_list()
    assert len(users) == 2

    assert users == [(john.id, "John", "PT"), (jane.id, "Jane", "EN")]


async def test_model_values_list_fields():
    await User(name="John", language="PT").create()
    await User(name="Jane", language="EN", description="Another simple description").create()

    users = await User.query().values_list(["name"])

    assert len(users) == 2

    assert users == [("John",), ("Jane",)]


async def test_model_values_list_flatten():
    await User(name="John", language="PT").create()
    await User(name="Jane", language="EN", description="Another simple description").create()

    users = await User.query().values_list(["name"], flat=True)

    assert len(users) == 2

    assert users == ["John", "Jane"]


@pytest.mark.parametrize(
    "value", [1, {"name": 1}, (1,), {"edgy"}], ids=["as-int", "as-dict", "as-tuple", "as-set"]
)
async def test_raise_exception(value):
    with pytest.raises(FieldDefinitionError):
        await User.query().values_list(value)


async def test_raise_exception_on_flatten_non_field():
    await User(name="John", language="PT").create()
    await User(name="Jane", language="EN", description="Another simple description").create()

    users = await User.query().values_list(["name"], flat=True)

    assert len(users) == 2

    with pytest.raises(FieldDefinitionError):
        await User.query().values_list("age", flat=True)


async def test_model_values_exclude_fields():
    await User(name="John", language="PT").create()
    await User(name="Jane", language="EN", description="Another simple description").create()

    users = await User.query().values_list(exclude=["name", "id"])
    assert len(users) == 2

    assert users == [("PT", None), ("EN", "Another simple description")]


async def test_model_values_exclude_and_include_fields():
    user1 = await User(name="John", language="PT").create()
    user2 = await User(
        name="Jane", language="EN", description="Another simple description"
    ).create()

    users = await User.query().values_list(["id"], exclude=["name"])
    assert len(users) == 2

    assert users == [(user1.id,), (user2.id,)]


async def test_model_values_exclude_none():
    user1 = await User(name="John", language="PT").create()
    user2 = await User(
        name="Jane", language="EN", description="Another simple description"
    ).create()

    users = await User.query().values_list(exclude_none=True)
    assert len(users) == 2

    assert users == [
        (user1.id, "John", "PT"),
        (user2.id, "Jane", "EN", "Another simple description"),
    ]


async def test_model_only_with_filter():
    await User(name="John", language="PT").create()
    user2 = await User(
        name="Jane", language="EN", description="Another simple description"
    ).create()

    users = await User.query(User.id == user2.id).values_list("name")
    assert len(users) == 1

    assert users == [("Jane",)]

    users = await User.query(User.id == 3).values_list("name")

    assert len(users) == 0

    assert users == []
