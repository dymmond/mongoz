from typing import AsyncGenerator, List, Union

import pydantic
import pytest

import mongoz
from mongoz.core.db import fields
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Student(mongoz.Document):
    student_scores: List[Union[str, float]] = fields.ArrayList()

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Student.objects.delete()
    yield
    await Student.objects.delete()


async def test_model_all() -> None:
    data = [["202405", 85.45], ["202406", 90.14]]

    await Student.objects.create(student_scores=data)

    student = await Student.objects.last()

    assert student.student_scores == data
