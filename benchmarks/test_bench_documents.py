"""Benchmarks for Document model instantiation and serialization."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import pytest

import mongoz
from benchmarks.conftest import client


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


@pytest.mark.benchmark
def test_bench_embedded_document_instantiation():
    """Benchmark creating EmbeddedDocument instances."""
    for _ in range(100):
        Course(
            code="CS101",
            name="Computer Science",
            start_date="2024-01-15",
            end_date="2024-06-15",
        )


@pytest.mark.benchmark
def test_bench_embedded_document_model_dump():
    """Benchmark serializing EmbeddedDocument to dict."""
    course = Course(
        code="CS101",
        name="Computer Science",
        start_date="2024-01-15",
        end_date="2024-06-15",
    )
    for _ in range(100):
        course.model_dump()


@pytest.mark.benchmark
def test_bench_embedded_document_model_dump_json():
    """Benchmark serializing EmbeddedDocument to JSON."""
    course = Course(
        code="CS101",
        name="Computer Science",
        start_date="2024-01-15",
        end_date="2024-06-15",
    )
    for _ in range(100):
        course.model_dump_json()


@pytest.mark.benchmark
def test_bench_embedded_document_with_nested():
    """Benchmark creating a Student with nested Course documents."""
    courses = [
        Course(
            code=f"CS{i}",
            name=f"Course {i}",
            start_date="2024-01-15",
            end_date="2024-06-15",
        )
        for i in range(5)
    ]
    for _ in range(50):
        Student(name="Test Student", roll_no=2024, courses=courses)


@pytest.mark.benchmark
def test_bench_document_model_dump_with_nested():
    """Benchmark serializing a Student with nested Course documents."""
    courses = [
        Course(
            code=f"CS{i}",
            name=f"Course {i}",
            start_date="2024-01-15",
            end_date="2024-06-15",
        )
        for i in range(5)
    ]
    student = Student(name="Test Student", roll_no=2024, courses=courses)
    for _ in range(50):
        student.model_dump()


@pytest.mark.benchmark
def test_bench_movie_model_instantiation():
    """Benchmark creating Movie document instances."""
    for _ in range(100):
        Movie(name="Benchmark Movie", year=2024, tags=["action", "sci-fi"])


@pytest.mark.benchmark
def test_bench_movie_model_dump():
    """Benchmark serializing a Movie document."""
    movie = Movie(name="Benchmark Movie", year=2024, tags=["action", "sci-fi"])
    for _ in range(100):
        movie.model_dump()
