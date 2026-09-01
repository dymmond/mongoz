"""Regression benchmarks for model construction, serialization, and hydration."""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

import pytest
from bson import ObjectId, encode

import mongoz
from benchmarks.conftest import client
from mongoz.core.db.documents.persistence import dump_document, validate_update_values


class Movie(mongoz.Document):
    name: str = mongoz.String()
    year: int = mongoz.Integer()
    tags: Optional[List[str]] = mongoz.Array(str, null=True)

    class Meta:
        registry = client
        database = "bench_db"


class Course(mongoz.EmbeddedDocument):
    code: str = mongoz.String()
    name: str = mongoz.String()
    start_date: datetime = mongoz.DateTime()
    end_date: datetime = mongoz.DateTime()


class Student(mongoz.Document):
    name: str = mongoz.String()
    roll_no: int = mongoz.Integer()
    courses: List[Course] = mongoz.Array(Course, default=[])

    class Meta:
        registry = client
        database = "bench_db"


def measure(benchmark: Any, function: Any) -> None:
    """Run a fixed warmup/repeat schedule through pytest-codspeed."""
    benchmark.pedantic(function, rounds=100, iterations=1, warmup_rounds=20)


@pytest.mark.benchmark(group="model-construction")
def test_bench_embedded_document_instantiation(benchmark: Any) -> None:
    measure(
        benchmark,
        lambda: Course(
            code="CS101", name="Computer Science", start_date="2024-01-15", end_date="2024-06-15"
        ),
    )


@pytest.mark.benchmark(group="serialization")
def test_bench_embedded_document_model_dump(benchmark: Any) -> None:
    course = Course(
        code="CS101", name="Computer Science", start_date="2024-01-15", end_date="2024-06-15"
    )
    measure(benchmark, course.model_dump)


@pytest.mark.benchmark(group="serialization")
def test_bench_embedded_document_model_dump_json(benchmark: Any) -> None:
    course = Course(
        code="CS101", name="Computer Science", start_date="2024-01-15", end_date="2024-06-15"
    )
    measure(benchmark, course.model_dump_json)


@pytest.mark.benchmark(group="model-construction")
def test_bench_embedded_document_with_nested(benchmark: Any) -> None:
    courses = [
        Course(code=f"CS{i}", name=f"Course {i}", start_date="2024-01-15", end_date="2024-06-15")
        for i in range(5)
    ]
    measure(benchmark, lambda: Student(name="Test Student", roll_no=2024, courses=courses))


@pytest.mark.benchmark(group="serialization")
def test_bench_document_model_dump_with_nested(benchmark: Any) -> None:
    courses = [
        Course(code=f"CS{i}", name=f"Course {i}", start_date="2024-01-15", end_date="2024-06-15")
        for i in range(5)
    ]
    student = Student(name="Test Student", roll_no=2024, courses=courses)
    measure(benchmark, student.model_dump)


@pytest.mark.benchmark(group="model-construction")
def test_bench_movie_model_instantiation(benchmark: Any) -> None:
    measure(benchmark, lambda: Movie(name="Benchmark Movie", year=2024, tags=["action", "sci-fi"]))


@pytest.mark.benchmark(group="serialization")
def test_bench_movie_model_dump(benchmark: Any) -> None:
    movie = Movie(name="Benchmark Movie", year=2024, tags=["action", "sci-fi"])
    measure(benchmark, movie.model_dump)


@pytest.mark.benchmark(group="hydration")
def test_bench_movie_hydration(benchmark: Any) -> None:
    row = {
        "_id": ObjectId("64b7abdecf2160b649ab6085"),
        "name": "Benchmark Movie",
        "year": 2024,
        "tags": ["action", "sci-fi"],
    }
    measure(benchmark, lambda: Movie.from_row(row))


@pytest.mark.benchmark(group="hydration")
def test_bench_bulk_hydration_100(benchmark: Any) -> None:
    rows = [
        {
            "_id": ObjectId(),
            "name": f"Benchmark Movie {index}",
            "year": 2024,
            "tags": ["action", "sci-fi"],
        }
        for index in range(100)
    ]
    measure(benchmark, lambda: [Movie.from_row(row) for row in rows])


@pytest.mark.benchmark(group="serialization")
def test_bench_persistence_payload(benchmark: Any) -> None:
    movie = Movie(name="Benchmark Movie", year=2024, tags=["action", "sci-fi"])
    measure(benchmark, lambda: dump_document(movie))


@pytest.mark.benchmark(group="serialization")
def test_bench_bson_encoding(benchmark: Any) -> None:
    payload = dump_document(Movie(name="Benchmark Movie", year=2024, tags=["action", "sci-fi"]))
    measure(benchmark, lambda: encode(payload))


@pytest.mark.benchmark(group="persistence")
def test_bench_update_payload_validation(benchmark: Any) -> None:
    measure(benchmark, lambda: validate_update_values(Movie, {"name": "Updated", "year": 2026}))
