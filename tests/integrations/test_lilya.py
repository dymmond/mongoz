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
from tests.settings import TEST_DATABASE_URL

pytestmark = pytest.mark.anyio
registry = mongoz.Registry(TEST_DATABASE_URL)


class Movie(Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()

    class Meta:
        registry = registry
        database = "test_db"


async def close_database() -> None:
    await registry.close()


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
    ],
    on_shutdown=[close_database],
)


@pytest.fixture(scope="module")
def integration_client():
    with TestClient(app) as client:
        yield client


async def test_lilya_integration_create(integration_client: TestClient) -> None:
    response = integration_client.post("/create", json={"name": "Barbie", "year": 2023})

    assert response.json()["name"] == "Barbie"
    assert response.json()["year"] == 2023
    assert response.status_code == 201


async def test_lilya_integration_read(integration_client: TestClient) -> None:
    integration_client.post("/create", json={"name": "Barbie", "year": 2023})
    response = integration_client.get("/all")

    assert response.json()["name"] == "Barbie"
    assert response.json()["year"] == 2023
    assert response.status_code == 200
