"""Pytest plugin enforcing Mongoz's warning baseline.

Known warning categories and their maximum counts live in ``pyproject.toml``.
The policy permits known warning debt to decrease, but rejects new categories
and growth in any known category. Pydantic deprecations are not allowlisted, so
their reintroduction fails the test session.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 only
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
WARNING_LIMITS = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"][
    "mongoz"
]["warning-ratchet"]
warning_counts: Counter[str] = Counter()


def pytest_unconfigure(config: pytest.Config) -> None:
    """Reset process-local counts only after config-time warnings were evaluated."""
    warning_counts.clear()


def pytest_warning_recorded(
    warning_message: Any,
    when: str,
    nodeid: str,
    location: tuple[str, int, str] | None,
) -> None:
    """Count every warning by its stable fully qualified category name."""
    category = warning_message.category
    warning_counts[f"{category.__module__}.{category.__qualname__}"] += 1


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Fail a passing session when warning categories or ceilings regress."""
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    violations = []

    for category, count in sorted(warning_counts.items()):
        limit = WARNING_LIMITS.get(category)
        if limit is None:
            violations.append(f"new warning category {category}: {count}")
        elif count > limit:
            violations.append(f"warning count grew for {category}: {count} > {limit}")

    if reporter is not None:
        reporter.write_sep("-", "warning ratchet")
        for category, count in sorted(warning_counts.items()):
            reporter.write_line(f"{category}: {count}/{WARNING_LIMITS.get(category, 0)}")
        for violation in violations:
            reporter.write_line(f"ERROR: {violation}", red=True)

    if exitstatus == pytest.ExitCode.OK and violations:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
