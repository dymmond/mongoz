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


async def prepare_database() -> None:
    await Movie.query().delete()


async def close_database() -> None:
    await Movie.query().delete()
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


async def clear_movies(request: Request):
    await Movie.query().delete()
    return Ok({})


app = Lilya(
    routes=[
        Path("/all", handler=get_movies),
        Path("/clear", handler=clear_movies, methods=["POST"]),
        Path("/create", handler=create_movies, methods=["POST"]),
    ],
    on_startup=[prepare_database],
    on_shutdown=[close_database],
)


@pytest.fixture(scope="module")
def integration_client():
    with TestClient(app) as client:
        yield client


async def test_lilya_integration_create(integration_client: TestClient) -> None:
    integration_client.post("/clear")
    response = integration_client.post(
        "/create", json={"name": "Barbie", "year": 2023}
    )

    assert response.json()["name"] == "Barbie"
    assert response.json()["year"] == 2023
    assert response.status_code == 201


async def test_lilya_integration_read(integration_client: TestClient) -> None:
    integration_client.post("/clear")
    integration_client.post("/create", json={"name": "Barbie", "year": 2023})
    response = integration_client.get("/all")

    assert response.json()["name"] == "Barbie"
    assert response.json()["year"] == 2023
    assert response.status_code == 200
