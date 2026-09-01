"""Regression benchmarks for immutable query and expression construction."""

from __future__ import annotations

from typing import Any

import pytest

from benchmarks.test_bench_documents import Movie, measure
from mongoz.core.db.datastructures import Order
from mongoz.core.db.querysets.expressions import Expression, SortExpression
from mongoz.core.db.querysets.operators import Q
from mongoz.utils.enums import ExpressionOperator


@pytest.mark.benchmark(group="expression")
def test_bench_expression_compile_eq(benchmark: Any) -> None:
    expression = Expression("name", ExpressionOperator.EQUAL, "test")
    measure(benchmark, expression.compile)


@pytest.mark.benchmark(group="expression")
def test_bench_expression_compile_regex(benchmark: Any) -> None:
    expression = Expression("name", ExpressionOperator.PATTERN, "test.*pattern")
    measure(benchmark, expression.compile)


@pytest.mark.benchmark(group="expression")
def test_bench_expression_compile_startswith(benchmark: Any) -> None:
    expression = Expression("name", ExpressionOperator.STARTSWITH, "prefix.*")
    measure(benchmark, expression.compile)


@pytest.mark.benchmark(group="expression")
def test_bench_expression_compile_many(benchmark: Any) -> None:
    expressions = [
        Expression("name", ExpressionOperator.EQUAL, "test"),
        Expression("age", ExpressionOperator.GREATER_THAN, 18),
        Expression("year", ExpressionOperator.LESS_THAN, 2024),
        Expression("email", ExpressionOperator.PATTERN, ".*@example.com"),
        Expression("status", ExpressionOperator.IN, ["active", "pending"]),
    ]
    measure(benchmark, lambda: Expression.compile_many(expressions))


@pytest.mark.benchmark(group="expression")
def test_bench_expression_unpack(benchmark: Any) -> None:
    query = {"name": "test", "year": {"$gt": 1990, "$lt": 2024}, "status": "active"}
    measure(benchmark, lambda: Expression.unpack(query))


@pytest.mark.benchmark(group="query-construction")
def test_bench_q_operator_construction(benchmark: Any) -> None:
    measure(benchmark, lambda: Q.gt("age", 18))


@pytest.mark.benchmark(group="query-construction")
def test_bench_q_logical_operators(benchmark: Any) -> None:
    expressions = [Q.eq("name", "test"), Q.gt("age", 18), Q.lt("year", 2024)]
    measure(benchmark, lambda: Q.and_(*expressions))


@pytest.mark.benchmark(group="query-construction")
def test_bench_sort_expression_compile(benchmark: Any) -> None:
    expression = SortExpression("name", Order.ASCENDING)
    measure(benchmark, expression.compile)


@pytest.mark.benchmark(group="query-construction")
def test_bench_manager_query_clone(benchmark: Any) -> None:
    query = Movie.objects.filter(year__gte=2020).sort("year")
    measure(benchmark, lambda: query.filter(name="Benchmark Movie"))


@pytest.mark.benchmark(group="query-construction")
def test_bench_queryset_query_clone(benchmark: Any) -> None:
    query = Movie.query(Movie.year >= 2020).sort("year")
    measure(benchmark, lambda: query.query(Movie.name == "Benchmark Movie"))
