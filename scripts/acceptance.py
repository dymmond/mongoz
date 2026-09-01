"""Run the complete local evidence suite with deterministic service cleanup."""

from __future__ import annotations

import os
import subprocess


def run(script: str, *, check: bool = True) -> None:
    """Run a canonical Hatch script outside the active parent environment."""
    environment = os.environ.copy()
    environment.pop("HATCH_ENV_ACTIVE", None)
    subprocess.run(["hatch", "run", script], env=environment, check=check)


def main() -> None:
    """Execute all acceptance gates and always tear down test topologies."""
    try:
        run("lint")
        run("format-check")
        run("typing")
        run("typing-negative")
        run("pre-commit-check")
        run("docs:validate")
        run("mongodb-standalone-up")
        run("mongodb-standalone-smoke")
        run("test:coverage")
        run("package:validate")
        run("mongodb-replica-set-up")
        run("mongodb-replica-set-smoke")
    finally:
        run("mongodb-replica-set-down", check=False)
        run("mongodb-standalone-down", check=False)


if __name__ == "__main__":
    main()
