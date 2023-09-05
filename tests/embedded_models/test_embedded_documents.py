import asyncio
import os
from typing import List

import pytest

import mongoz
from mongoz import Document, EmbeddedDocument, Registry

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
