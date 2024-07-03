from typing import List

import pytest

import mongoz
from mongoz import Document, EmbeddedDocument
from tests.conftest import client

pytestmark = pytest.mark.anyio


class Actor(EmbeddedDocument):
    name: str = mongoz.String()
    price: float = mongoz.Decimal(max_digits=5, decimal_places=2, null=True)


class Movie(Document):
    actors: List[Actor] = mongoz.Array(Actor)

    class Meta:
        registry = client
        database = "test_db"


async def test_embedded_model() -> None:
    actor = Actor(name="Tom Hanks", price=100.00)

    await Movie(
        actors=[actor],
        name="Saving Private Ryan",
    ).create()

    movie = await Movie.objects.last()

    assert movie.actors[0].name == "Tom Hanks"
    assert float(str(movie.actors[0].price)) == 100.00
