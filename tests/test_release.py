import re
from pathlib import Path

import pytest

from scripts import release, validate_package as package_validation


@pytest.fixture(scope="session", autouse=True)
def registry_lifecycle() -> None:
    """Override the database lifecycle for release-only checks."""


@pytest.fixture(autouse=True)
def test_database() -> None:
    """Override database cleanup because these checks never use MongoDB."""


def test_release_identity_matches_prepared_notes() -> None:
    version = release.canonical_version()

    assert version == "0.14.0"
    assert release.release_notes(version).startswith("### Added")


def test_release_version_rejects_other_release_lines(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    version_source = tmp_path / "__init__.py"
    version_source.write_text('__version__ = "1.0.0"\n', encoding="utf-8")
    monkeypatch.setattr(release, "VERSION_SOURCE", version_source)

    with pytest.raises(RuntimeError, match="0.MINOR.PATCH"):
        release.canonical_version()


def test_release_notes_reject_missing_version(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    notes = tmp_path / "release-notes.md"
    notes.write_text("# Release Notes\n\n## Unreleased\n", encoding="utf-8")
    monkeypatch.setattr(release, "RELEASE_NOTES", notes)

    with pytest.raises(RuntimeError, match="expected one release-note section"):
        release.release_notes("0.14.0")


def test_release_notes_reject_test_language(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    notes = tmp_path / "release-notes.md"
    body = "\n".join(release.REQUIRED_RELEASE_TOPICS["0.14.0"])
    notes.write_text(
        f"# Release Notes\n\n## Unreleased\n\n## 0.14.0\n\n{body}\n\nTests passed.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(release, "RELEASE_NOTES", notes)

    with pytest.raises(RuntimeError, match="must not mention tests"):
        release.release_notes("0.14.0")


def test_release_tag_must_match_version() -> None:
    with pytest.raises(RuntimeError, match="does not match canonical version"):
        release.validate_tag("0.14.1", "0.14.0")


def test_release_rejects_missing_distribution_pair(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(package_validation, "DIST", tmp_path)

    with pytest.raises(RuntimeError, match="expected only mongoz-0.14.0"):
        package_validation.artifact_pair()


def test_release_workflow_builds_once_and_reuses_artifacts() -> None:
    workflow = (release.ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")

    assert workflow.count("hatch build --clean") == 1
    assert "hatch run package:validate --no-build" in workflow
    assert workflow.index("actions/attest@") < workflow.index("pypa/gh-action-pypi-publish@")
    assert "PYPI_TOKEN" not in workflow
    assert "TWINE_PASSWORD" not in workflow


def test_workflow_actions_use_immutable_commits() -> None:
    workflows = release.ROOT / ".github" / "workflows"
    references = []
    for workflow in workflows.glob("*.yml"):
        references.extend(re.findall(r"uses:\s*[\"']?[^\s\"']+@([^\s\"']+)", workflow.read_text()))

    assert references
    assert all(re.fullmatch(r"[0-9a-f]{40}", reference) for reference in references)
