import json

import pytest
from esmerald import Esmerald, Gateway, JSONResponse, Request, get, post
from esmerald.testclient import EsmeraldTestClient

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


@post("/create")
async def create_movies(request: Request) -> JSONResponse:
    data = await request.json()
    movie = await Movie(**data).create()
    return JSONResponse(json.loads(movie.model_dump_json()))


@get("/all")
async def get_movies(request: Request) -> JSONResponse:
    movie = await Movie.query().get()
    return JSONResponse(json.loads(movie.model_dump_json()))


app = Esmerald(
    routes=[
        Gateway(handler=get_movies),
        Gateway(handler=create_movies),
    ]
)


async def test_esmerald_integration_create() -> None:
    with EsmeraldTestClient(app) as client:
        response = client.post("/create", json={"name": "Barbie", "year": 2023})

        assert response.json()["name"] == "Barbie"
        assert response.json()["year"] == 2023
        assert response.status_code == 201


async def test_esmerald_integration_read() -> None:
    with EsmeraldTestClient(app) as client:
        client.post("/create", json={"name": "Barbie", "year": 2023})
        response = client.get("/all")

        assert response.json()["name"] == "Barbie"
        assert response.json()["year"] == 2023
        assert response.status_code == 200
