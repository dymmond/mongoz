from typing import List

import mongoz
from mongoz import Document, EmbeddedDocument

database_uri = "mongodb://localhost:27017"
registry = mongoz.Registry(database_uri)


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
    name: str = mongoz.String()
    director: Crew = mongoz.Embed(Crew)
    genre: Genre = mongoz.Embed(Genre)
    year: int = mongoz.Integer()

    class Meta:
        registry = registry
        database = "my_db"
