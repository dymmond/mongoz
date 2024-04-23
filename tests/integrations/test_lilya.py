import json

import pytest
from lilya import status
from lilya.apps import Lilya
from lilya.requests import Request
from lilya.responses import Ok
from lilya.routing import Path
from lilya.testclient import TestClient

import mongoz
from mongoz import Document
from tests.conftest import client

pytestmark = pytest.mark.anyio


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()

    class Meta:
        registry = client
        database = "test_db"


@pytest.fixture(scope="module", autouse=True)
async def prepare_database() -> None:
    await Movie.query().delete()


async def create_movies(request: Request):
    data = await request.json()
    movie = await Movie(**data).create()
    return Ok(
        json.loads(movie.model_dump_json()),
        status_code=status.HTTP_201_CREATED,
    )


async def get_movies(request: Request):
    movie = await Movie.query().get()
    return Ok(json.loads(movie.model_dump_json()))


app = Lilya(
    routes=[
        Path("/all", handler=get_movies),
        Path("/create", handler=create_movies, methods=["POST"]),
    ]
)


async def test_lilya_integration_create() -> None:
    with TestClient(app) as client:
        response = client.post("/create", json={"name": "Barbie", "year": 2023})

        assert response.json()["name"] == "Barbie"
        assert response.json()["year"] == 2023
        assert response.status_code == 201


async def test_lilya_integration_read() -> None:
    with TestClient(app) as client:
        client.post("/create", json={"name": "Barbie", "year": 2023})
        response = client.get("/all")

        assert response.json()["name"] == "Barbie"
        assert response.json()["year"] == 2023
        assert response.status_code == 200
