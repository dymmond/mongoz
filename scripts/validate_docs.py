"""Validate documentation sources, examples, compatibility pages, and Zensical output."""

from __future__ import annotations

import ast
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from docs_pipeline import INCLUDE, DocsPipelineError, prepare_docs_tree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "en" / "docs"
GENERATED = ROOT / "docs" / "generated"
EXAMPLES = ROOT / "docs_src"
PYTHON_FENCE = re.compile(
    r"^```(?:python|py)(?:[^\n]*)\n(?P<body>.*?)^```[ \t]*$",
    re.MULTILINE | re.DOTALL,
)

# Complete, side-effect-free programs. Each is executed, not merely compiled.
EXECUTABLE_EXAMPLES = {
    Path("examples/document.py"),
    Path("examples/query.py"),
    Path("examples/settings.py"),
}

# Host-application sketches with intentionally fictional imports. They remain syntax checked.
PSEUDOCODE_EXAMPLES = {
    Path("examples/application.py"),
}

LEGACY_ROUTES = {
    "documents.md": "concepts/documents.md",
    "embedded-documents.md": "concepts/embedded-documents.md",
    "fields.md": "reference/fields.md",
    "queries.md": "guides/querying.md",
    "managers.md": "concepts/managers-querysets.md",
    "signals.md": "guides/signals.md",
    "settings.md": "reference/signals-errors-settings.md",
    "registry.md": "concepts/registry-boundaries.md",
    "exceptions.md": "reference/signals-errors-settings.md",
    "production.md": "operations/index.md",
    "tips-and-tricks.md": "guides/index.md",
    "contributing.md": "project/contributing.md",
    "sponsorship.md": "project/sponsorship.md",
}


def _tree_digest(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def validate_preparation() -> None:
    """Prove include expansion is complete and deterministic."""
    prepare_docs_tree(SOURCE, GENERATED, include_roots=(ROOT, SOURCE))
    first = _tree_digest(GENERATED)
    prepare_docs_tree(SOURCE, GENERATED, include_roots=(ROOT, SOURCE))
    second = _tree_digest(GENERATED)
    if first != second:
        raise RuntimeError("documentation preparation is not deterministic")
    leftovers = [
        path.relative_to(ROOT)
        for path in GENERATED.rglob("*.md")
        if INCLUDE.search(path.read_text(encoding="utf-8"))
    ]
    if leftovers:
        raise RuntimeError(f"unexpanded documentation includes: {leftovers}")

    with tempfile.TemporaryDirectory(prefix="mongoz-docs-pipeline-") as directory:
        fixture = Path(directory)
        source = fixture / "source"
        output = fixture / "generated"
        source.mkdir()
        (source / "leaf.md").write_text("Nested proof.\n", encoding="utf-8")
        (source / "middle.md").write_text("{!> leaf.md !}\n", encoding="utf-8")
        (source / "index.md").write_text("{!> middle.md !}\n", encoding="utf-8")
        prepare_docs_tree(source, output, include_roots=(source,))
        if (output / "index.md").read_text(encoding="utf-8") != "Nested proof.\n":
            raise RuntimeError("nested documentation includes were not expanded")
        valid = _tree_digest(output)

        (source / "middle.md").write_text("{!> index.md !}\n", encoding="utf-8")
        try:
            prepare_docs_tree(source, output, include_roots=(source,))
        except DocsPipelineError:
            pass
        else:
            raise RuntimeError("cyclic documentation include was accepted")
        if _tree_digest(output) != valid:
            raise RuntimeError("failed preparation replaced the last valid generated tree")


def validate_source_examples() -> tuple[int, int, int]:
    """Compile every snippet and execute the intentionally runnable subset."""
    paths = {path.relative_to(EXAMPLES) for path in EXAMPLES.rglob("*.py")}
    missing = (EXECUTABLE_EXAMPLES | PSEUDOCODE_EXAMPLES) - paths
    if missing:
        raise RuntimeError(f"classified documentation examples do not exist: {sorted(missing)}")
    fragments = paths - EXECUTABLE_EXAMPLES - PSEUDOCODE_EXAMPLES
    for relative in sorted(paths):
        flags = (
            0
            if relative in EXECUTABLE_EXAMPLES | PSEUDOCODE_EXAMPLES
            else ast.PyCF_ALLOW_TOP_LEVEL_AWAIT
        )
        source = (EXAMPLES / relative).read_text(encoding="utf-8")
        compile(source, str(EXAMPLES / relative), "exec", flags=flags)
    for relative in sorted(EXECUTABLE_EXAMPLES):
        subprocess.run([sys.executable, str(EXAMPLES / relative)], cwd=ROOT, check=True)
    return len(EXECUTABLE_EXAMPLES), len(fragments), len(PSEUDOCODE_EXAMPLES)


def validate_markdown_examples() -> int:
    """Syntax-check every rendered Python fence, including top-level await fragments."""
    count = 0
    for markdown in sorted(GENERATED.rglob("*.md")):
        content = markdown.read_text(encoding="utf-8")
        for number, match in enumerate(PYTHON_FENCE.finditer(content), start=1):
            compile(
                match.group("body"),
                f"{markdown.relative_to(ROOT)}:python-fence-{number}",
                "exec",
                flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
            )
            count += 1
    return count


def validate_compatibility_routes() -> None:
    """Require every high-value pre-migration route and archived Portuguese route."""
    failures: list[str] = []
    for legacy, target in LEGACY_ROUTES.items():
        path = SOURCE / legacy
        if not path.is_file() or target not in path.read_text(encoding="utf-8"):
            failures.append(f"{legacy} -> {target}")
        portuguese = SOURCE / "pt" / legacy
        if not portuguese.is_file():
            failures.append(f"pt/{legacy} (archived route missing)")
    if not (SOURCE / "pt" / "index.md").is_file():
        failures.append("pt/index.md (archived route missing)")
    if failures:
        raise RuntimeError(
            "documentation compatibility routes are incomplete:\n" + "\n".join(failures)
        )


def build_site() -> None:
    """Run the authoritative strict Zensical build."""
    subprocess.run(
        [sys.executable, "scripts/docs.py", "build", "--clean-cache"],
        cwd=ROOT,
        check=True,
    )


def main() -> None:
    validate_preparation()
    executable, fragments, pseudocode = validate_source_examples()
    markdown = validate_markdown_examples()
    validate_compatibility_routes()
    build_site()
    print(
        "Validated "
        f"{executable} executable snippets, {fragments} fragments, "
        f"{pseudocode} pseudocode files, {markdown} rendered Python fences, "
        "legacy routes, recursive deterministic preparation, failure rollback, "
        "and a strict Zensical build."
    )


if __name__ == "__main__":
    main()
