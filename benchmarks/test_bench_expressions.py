"""Benchmarks for Expression compilation and Q operator construction."""

from __future__ import annotations

import pytest

from mongoz.core.db.querysets.expressions import Expression, SortExpression
from mongoz.core.db.querysets.operators import Q
from mongoz.utils.enums import ExpressionOperator


@pytest.mark.benchmark
def test_bench_expression_compile_eq():
    """Benchmark compiling a simple equality expression."""
    expr = Expression(key="name", operator=ExpressionOperator.EQUAL, value="test")
    for _ in range(100):
        expr.compile()


@pytest.mark.benchmark
def test_bench_expression_compile_regex():
    """Benchmark compiling a regex expression."""
    expr = Expression(
        key="name", operator=ExpressionOperator.PATTERN, value="test.*pattern"
    )
    for _ in range(100):
        expr.compile()


@pytest.mark.benchmark
def test_bench_expression_compile_startswith():
    """Benchmark compiling a startswith expression."""
    expr = Expression(
        key="name", operator=ExpressionOperator.STARTSWITH, value="prefix"
    )
    for _ in range(100):
        expr.compile()


@pytest.mark.benchmark
def test_bench_expression_compile_many():
    """Benchmark compiling multiple expressions at once."""
    expressions = [
        Expression(key="name", operator=ExpressionOperator.EQUAL, value="test"),
        Expression(key="age", operator=ExpressionOperator.GREATER_THAN, value=18),
        Expression(key="year", operator=ExpressionOperator.LESS_THAN, value=2024),
        Expression(
            key="email", operator=ExpressionOperator.PATTERN, value=".*@example.com"
        ),
        Expression(
            key="status", operator=ExpressionOperator.IN, value=["active", "pending"]
        ),
    ]
    for _ in range(100):
        Expression.compile_many(expressions)


@pytest.mark.benchmark
def test_bench_expression_unpack():
    """Benchmark unpacking a dictionary into expressions."""
    d = {
        "name": "test",
        "year": {"$gt": 1990, "$lt": 2024},
        "status": "active",
    }
    for _ in range(100):
        Expression.unpack(d)


@pytest.mark.benchmark
def test_bench_q_operator_construction():
    """Benchmark constructing Q operator expressions."""
    for _ in range(100):
        Q.eq("name", "test")
        Q.neq("status", "inactive")
        Q.gt("age", 18)
        Q.lt("year", 2024)
        Q.gte("score", 80)
        Q.lte("price", 100.0)


@pytest.mark.benchmark
def test_bench_q_in_operator():
    """Benchmark constructing Q in/not_in expressions."""
    values = ["active", "pending", "approved", "rejected"]
    for _ in range(100):
        Q.in_("status", values)
        Q.not_in("status", values)


@pytest.mark.benchmark
def test_bench_q_logical_operators():
    """Benchmark constructing logical Q operators (and, or, nor)."""
    expr1 = Q.eq("name", "test")
    expr2 = Q.gt("age", 18)
    expr3 = Q.lt("year", 2024)
    for _ in range(100):
        Q.and_(expr1, expr2, expr3)
        Q.or_(expr1, expr2, expr3)


@pytest.mark.benchmark
def test_bench_q_ordering():
    """Benchmark constructing ordering expressions."""
    for _ in range(100):
        Q.asc("name")
        Q.desc("created_at")
        Q.asc("year")
        Q.desc("score")


@pytest.mark.benchmark
def test_bench_sort_expression_compile():
    """Benchmark compiling sort expressions."""
    from mongoz.core.db.datastructures import Order

    sort_expr = SortExpression(key="name", direction=Order.ASCENDING)
    for _ in range(100):
        sort_expr.compile()
