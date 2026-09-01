from pathlib import Path

import pytest

from scripts import docs_pipeline

pytestmark = pytest.mark.anyio


async def test_documentation_include_cannot_escape_configured_roots(tmp_path: Path) -> None:
    source_root = tmp_path / "docs"
    source_root.mkdir()
    source = source_root / "page.md"
    outside = tmp_path / "secret.txt"
    outside.write_text("must not be included", encoding="utf-8")

    with pytest.raises(docs_pipeline.DocsPipelineError, match="Include not found"):
        docs_pipeline.render_markdown("{!> ../secret.txt !}", source, (source_root,))


async def test_zensical_start_failure_is_a_docs_pipeline_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("zensical")

    monkeypatch.setattr(docs_pipeline.subprocess, "run", fail)

    with pytest.raises(docs_pipeline.DocsPipelineError, match="Could not execute Zensical"):
        docs_pipeline.run_zensical(tmp_path, tmp_path / "mkdocs.yaml", "build")
