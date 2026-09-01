import json

import pytest
from ravyn import Gateway, JSONResponse, Ravyn, Request, get, post
from ravyn.testclient import RavynTestClient

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


@post("/create")
async def create_movies(request: Request) -> JSONResponse:
    data = await request.json()
    movie = await Movie(**data).create()
    return JSONResponse(json.loads(movie.model_dump_json()))


@get("/all")
async def get_movies(request: Request) -> JSONResponse:
    movie = await Movie.query().get()
    return JSONResponse(json.loads(movie.model_dump_json()))


@post("/clear")
async def clear_movies(request: Request) -> JSONResponse:
    await Movie.query().delete()
    return JSONResponse({})


app = Ravyn(
    routes=[
        Gateway(handler=get_movies),
        Gateway(handler=clear_movies),
        Gateway(handler=create_movies),
    ],
    on_startup=[prepare_database],
    on_shutdown=[close_database],
)


@pytest.fixture(scope="module")
def integration_client():
    with RavynTestClient(app) as client:
        yield client


async def test_ravyn_integration_create(
    integration_client: RavynTestClient,
) -> None:
    integration_client.post("/clear")
    response = integration_client.post(
        "/create", json={"name": "Barbie", "year": 2023}
    )

    assert response.json()["name"] == "Barbie"
    assert response.json()["year"] == 2023
    assert response.status_code == 201


async def test_ravyn_integration_read(
    integration_client: RavynTestClient,
) -> None:
    integration_client.post("/clear")
    integration_client.post("/create", json={"name": "Barbie", "year": 2023})
    response = integration_client.get("/all")

    assert response.json()["name"] == "Barbie"
    assert response.json()["year"] == 2023
    assert response.status_code == 200
