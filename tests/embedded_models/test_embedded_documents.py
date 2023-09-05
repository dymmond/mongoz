import asyncio
import os
from typing import List

import pytest

import mongoz
from mongoz import Document, EmbeddedDocument, Registry
from mongoz.exceptions import InvalidKeyError

pytestmark = pytest.mark.asyncio

database_uri = os.environ.get("DATABASE_URI", "mongodb://localhost:27017")
client = Registry(database_uri, event_loop=asyncio.get_running_loop)
db = client.get_database("test_db")


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


async def xtest_embedded_model() -> None:
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
    ).insert()

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
