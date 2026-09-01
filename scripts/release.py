"""Validate release identity and extract committed release notes."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    from .release_metadata import read_canonical_version
except ImportError:  # pragma: no cover - direct script execution
    from release_metadata import read_canonical_version

ROOT = Path(__file__).resolve().parents[1]
VERSION_SOURCE = ROOT / "mongoz" / "__init__.py"
RELEASE_NOTES = ROOT / "docs" / "en" / "docs" / "release-notes.md"
HEADING_PATTERN = re.compile(r"^## (?P<title>[^\n]+)$", re.MULTILINE)
REQUIRED_RELEASE_TOPICS = {
    "0.14.0": (
        "PyMongo",
        "Registry",
        "query",
        "session",
        "update",
        "save",
        "delete",
        "index",
        "transaction",
        "aggregation",
        "bulk",
        "ty",
        "signal",
        "warning",
        "performance",
        "security",
        "Pydantic",
        "Zensical",
        "migration",
    )
}


def canonical_version() -> str:
    """Read the sole package version without importing repository code."""
    return read_canonical_version(VERSION_SOURCE)


def release_notes(version: str) -> str:
    """Return one complete version section from the canonical release-note history."""
    content = RELEASE_NOTES.read_text(encoding="utf-8")
    headings = list(HEADING_PATTERN.finditer(content))
    if not headings or headings[0].group("title") != "Unreleased":
        raise RuntimeError("release notes must begin with an Unreleased section")
    unreleased_end = headings[1].start() if len(headings) > 1 else len(content)
    if content[headings[0].end() : unreleased_end].strip():
        raise RuntimeError("Unreleased release notes must be empty before publication")
    matches = [heading for heading in headings if heading.group("title") == version]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one release-note section for {version}, found {len(matches)}"
        )
    match = matches[0]
    index = headings.index(match)
    end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
    body = content[match.end() : end].strip()
    if not body:
        raise RuntimeError(f"release-note section for {version} is empty")
    if re.search(r"\b(?:pytest|test(?:s|ing|ed)?)\b", body, flags=re.IGNORECASE):
        raise RuntimeError(f"release-note section for {version} must not mention tests")
    missing = [
        topic
        for topic in REQUIRED_RELEASE_TOPICS.get(version, ())
        if re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(topic)}s?(?![A-Za-z0-9_])",
            body,
            flags=re.IGNORECASE,
        )
        is None
    ]
    if missing:
        raise RuntimeError(f"release-note section for {version} is missing topics: {missing}")
    return body + "\n"


def validate_tag(tag: str, version: str) -> None:
    """Require an exact version tag pointing at the checked-out commit."""
    if tag != version:
        raise RuntimeError(f"release tag {tag!r} does not match canonical version {version!r}")
    tagged = subprocess.run(
        ["git", "rev-list", "-n", "1", tag],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    current = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if tagged != current:
        raise RuntimeError(
            f"release tag {tag!r} points to {tagged}, not checked-out commit {current}"
        )


def validate_unpublished(version: str) -> None:
    """Fail when PyPI already has the exact immutable version."""
    request = urllib.request.Request(
        f"https://pypi.org/pypi/mongoz/{version}/json",
        headers={"User-Agent": "mongoz-release-validation"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15):
            pass
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return
        raise RuntimeError(f"PyPI version lookup failed with HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"PyPI version lookup failed: {exc.reason}") from exc
    raise RuntimeError(f"mongoz {version} already exists on PyPI and cannot be overwritten")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    validate = subcommands.add_parser("validate", help="validate release identity and notes")
    validate.add_argument("--tag", help="require an exact Git tag at HEAD")
    validate.add_argument("--check-pypi", action="store_true")
    notes = subcommands.add_parser("notes", help="write the current release body")
    notes.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    version = canonical_version()
    body = release_notes(version)
    if args.command == "validate":
        if args.tag:
            validate_tag(args.tag, version)
        if args.check_pypi:
            validate_unpublished(version)
        print(f"Validated Mongoz release identity {version}")
        return
    if args.output:
        args.output.write_text(body, encoding="utf-8")
    else:
        sys.stdout.write(body)


if __name__ == "__main__":
    main()
