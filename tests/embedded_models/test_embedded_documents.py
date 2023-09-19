from typing import List

import pytest

import mongoz
from mongoz import Document, EmbeddedDocument
from mongoz.exceptions import InvalidKeyError
from tests.conftest import client

pytestmark = pytest.mark.anyio


class Award(EmbeddedDocument):
    name: str = mongoz.String()


class Crew(EmbeddedDocument):
    award: Award = mongoz.Embed(Award)
    name: str = mongoz.String()


class Actor(EmbeddedDocument):
    name: str = mongoz.String()


class Genre(EmbeddedDocument):
    title: str = mongoz.String()


class Movie(Document):
    actors: List[Actor] = mongoz.Array(Actor)
    director: Crew = mongoz.Embed(Crew)
    name: str = mongoz.String()
    genre: Genre = mongoz.Embed(Genre)
    year: int = mongoz.Integer()

    class Meta:
        registry = client
        database = "test_db"


async def test_embedded_model() -> None:
    actor = Actor(name="Tom Hanks")
    genre = Genre(title="Action")
    award = Award(name="Academy Award")
    director = Crew(name="Steven Spielberg", award=award)

    await Movie(
        actors=[actor],
        name="Saving Private Ryan",
        director=director,
        year=1990,
        genre=genre,
    ).create()

    movie = await Movie.query(Movie.genre.title == "Action").get()
    assert movie.name == "Saving Private Ryan"

    movie = await Movie.query({Movie.genre.title: "Action"}).get()
    assert movie.name == "Saving Private Ryan"

    movie = await Movie.query({"genre.title": "Action"}).get()
    assert movie.name == "Saving Private Ryan"

    movie = await Movie.query(Movie.genre == genre).get()
    assert movie.name == "Saving Private Ryan"

    movie = await Movie.query(Movie.actors == [actor]).get()
    assert movie.name == "Saving Private Ryan"

    movie = await Movie.query(Movie.director.award.name == "Academy Award").get()
    assert movie.name == "Saving Private Ryan"

    movie = await Movie.query(Movie.director.award == award).get()
    assert movie.name == "Saving Private Ryan"

    with pytest.raises(InvalidKeyError):
        await Movie.query(Movie.director.award.year == 1990).get()  # type: ignore
