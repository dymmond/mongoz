"""Run the complete local evidence suite with deterministic service cleanup."""

from __future__ import annotations

import os
import subprocess
import sys


def run(script: str, *, check: bool = True) -> None:
    """Run a canonical Hatch script outside the active parent environment."""
    environment = os.environ.copy()
    environment.pop("HATCH_ENV_ACTIVE", None)
    subprocess.run(["hatch", "run", script], env=environment, check=check)


def main() -> None:
    """Execute all acceptance gates and always tear down test topologies."""
    primary_error: BaseException | None = None
    try:
        run("lint")
        run("format-check")
        run("typing")
        run("typing-negative")
        run("pre-commit-check")
        run("release:validate")
        run("security:audit")
        run("docs:validate")
        run("mongodb-standalone-up")
        run("mongodb-standalone-smoke")
        run("test:coverage")
        run("package:validate")
        run("mongodb-replica-set-up")
        run("mongodb-replica-set-smoke")
    except BaseException as exc:
        primary_error = exc
    finally:
        cleanup_errors = []
        for script in ("mongodb-replica-set-down", "mongodb-standalone-down"):
            try:
                run(script)
            except BaseException as exc:
                cleanup_errors.append(exc)
        if primary_error is not None:
            if cleanup_errors:
                print(
                    "Acceptance cleanup also failed: "
                    + "; ".join(str(error) for error in cleanup_errors),
                    file=sys.stderr,
                )
            raise primary_error
        if cleanup_errors:
            raise RuntimeError(
                "Acceptance cleanup failed: " + "; ".join(str(error) for error in cleanup_errors)
            )


if __name__ == "__main__":
    main()
