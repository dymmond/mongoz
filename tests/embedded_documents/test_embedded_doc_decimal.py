from typing import List

import pytest
from pydantic import ValidationError

import mongoz
from mongoz import Document, EmbeddedDocument
from tests.conftest import client

pytestmark = pytest.mark.anyio


class Actor(EmbeddedDocument):
    name: str = mongoz.String()
    price: float = mongoz.Decimal(
        max_digits=5, decimal_places=2, null=True, maximum=150, minimum=50
    )


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


async def test_embedded_model_with_decimal_place() -> None:
    actor = Actor(name="Tom Hanks", price=100.455)

    await Movie(
        actors=[actor],
        name="Saving Private Ryan",
    ).create()
    movie = await Movie.objects.last()

    assert movie.actors[0].name == "Tom Hanks"
    assert float(str(movie.actors[0].price)) == 100.45


async def test_embedded_model_with_max() -> None:
    with pytest.raises(ValidationError):
        Actor(name="Tom Hanks", price=200.455)


async def test_embedded_model_with_min() -> None:
    with pytest.raises(ValidationError):
        Actor(name="Tom Hanks", price=10.455)


async def test_embedded_model_with_max_digit() -> None:
    with pytest.raises(ValidationError):
        Actor(name="Tom Hanks", price=2100.455)
