"""Validate documentation includes, Python examples, and strict site builds."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_SOURCE = ROOT / "docs_src"
INCLUDE_PATTERN = re.compile(r"\{!>?\s*(?P<path>.+?)\s*!\}")

# These examples are complete, side-effect-free programs and must execute.
EXECUTABLE_EXAMPLES = {
    Path("documents/abstract/simple.py"),
    Path("documents/declaring_models.py"),
    Path("documents/default_model.py"),
    Path("documents/embed.py"),
    Path("documents/registry/nutshell.py"),
    Path("documents/tablename/model_diff_tn.py"),
    Path("documents/tablename/model_no_tablename.py"),
    Path("documents/tablename/model_with_tablename.py"),
    Path("managers/example.py"),
    Path("queries/document.py"),
    Path("queries/embed.py"),
    Path("quickstart/quickstart.py"),
    Path("settings/custom_settings.py"),
}

# These are project-layout pseudocode; imports need the fictional host project.
PSEUDOCODE_EXAMPLES = {
    Path("tips/connection.py"),
    Path("tips/lru.py"),
    Path("tips/models.py"),
    Path("tips/settings.py"),
}


def validate_includes() -> None:
    """Fail when a Markdown include target does not exist."""
    failures = []
    for markdown_path in sorted((ROOT / "docs").rglob("*.md")):
        text = markdown_path.read_text(encoding="utf-8")
        for match in INCLUDE_PATTERN.finditer(text):
            target = (markdown_path.parent / match.group("path")).resolve()
            if not target.is_file():
                failures.append(f"{markdown_path.relative_to(ROOT)} -> {target}")
    if failures:
        raise RuntimeError("broken documentation includes:\n" + "\n".join(failures))


def validate_python_examples() -> None:
    """Compile all examples and execute the self-contained subset."""
    example_paths = {path.relative_to(DOCS_SOURCE) for path in DOCS_SOURCE.rglob("*.py")}
    missing = (EXECUTABLE_EXAMPLES | PSEUDOCODE_EXAMPLES) - example_paths
    if missing:
        raise RuntimeError(f"classified documentation examples do not exist: {sorted(missing)}")

    fragment_examples = example_paths - EXECUTABLE_EXAMPLES - PSEUDOCODE_EXAMPLES
    for relative_path in sorted(example_paths):
        path = DOCS_SOURCE / relative_path
        flags = ast.PyCF_ALLOW_TOP_LEVEL_AWAIT if relative_path in fragment_examples else 0
        compile(path.read_text(encoding="utf-8"), str(path), "exec", flags=flags)

    for relative_path in sorted(EXECUTABLE_EXAMPLES):
        subprocess.run(
            [
                sys.executable,
                "-W",
                "ignore:Field name:UserWarning",
                str(DOCS_SOURCE / relative_path),
            ],
            cwd=ROOT,
            check=True,
        )

    print(
        "Validated "
        f"{len(EXECUTABLE_EXAMPLES)} executable examples, "
        f"{len(fragment_examples)} include fragments, and "
        f"{len(PSEUDOCODE_EXAMPLES)} pseudocode examples."
    )


def build_sites() -> None:
    """Build every configured language with strict link validation."""
    with tempfile.TemporaryDirectory(prefix="mongoz-docs-") as output_dir:
        output_root = Path(output_dir)
        for language in ("en", "pt"):
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "mkdocs",
                    "build",
                    "--strict",
                    "--site-dir",
                    str(output_root / language),
                ],
                cwd=ROOT / "docs" / language,
                check=True,
            )


def main() -> None:
    """Run the complete pre-Zensical documentation gate."""
    validate_includes()
    validate_python_examples()
    build_sites()


if __name__ == "__main__":
    main()
