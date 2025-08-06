from decimal import Decimal
from typing import AsyncGenerator, List

import pydantic
import pytest

import mongoz
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]


class Badges(mongoz.EmbeddedDocument):
    score: Decimal = mongoz.Decimal(max_digits=5, decimal_places=2, null=True)
    name: str = mongoz.String()


class Achievement(mongoz.Document):
    name: str = mongoz.String()
    total_score: Decimal = mongoz.Decimal(
        max_digits=5, decimal_places=2, null=True
    )  # noqa
    badges: List[Badges] = mongoz.Array(Badges, null=True)

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator:
    await Achievement.objects.delete()
    yield
    await Achievement.objects.delete()


async def test_decimal_on_update() -> None:
    badges = [{"name": "badge1", "score": "083.33"}]
    await Achievement.objects.create(name="Batman", total_score="22.246")

    arch = await Achievement.objects.last()

    arch.total_score = Decimal("28")
    await arch.save()

    arch = await Achievement.objects.last()

    await arch.update(total_score=Decimal("30"))

    arch = await Achievement.objects.last()

    await Achievement.objects.filter().update(
        total_score=Decimal("40"), badges=badges
    )

    arch = await Achievement.objects.last()
