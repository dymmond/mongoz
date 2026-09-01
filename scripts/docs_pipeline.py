"""Deterministic preparation and Zensical execution for Mongoz documentation."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

INCLUDE = re.compile(r"\{!>\s*(?P<path>[^!]+?)\s*!}")
FENCED_INCLUDE = re.compile(
    r"```(?P<language>[^\n`]*)\n[ \t]*\{!>\s*(?P<path>[^!]+?)\s*!}[ \t]*\n```",
    re.MULTILINE,
)
MARKDOWN_SUFFIXES = {".md", ".markdown"}
LANGUAGES = {
    ".bash": "bash",
    ".js": "javascript",
    ".json": "json",
    ".py": "python",
    ".sh": "bash",
    ".toml": "toml",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
}


class DocsPipelineError(RuntimeError):
    """Raised when documentation preparation or Zensical execution fails."""


def _normalise(content: str) -> str:
    return content.replace("\r\n", "\n").replace("\r", "\n")


def _language(path: Path) -> str:
    if path.name.lower() == "dockerfile":
        return "dockerfile"
    return LANGUAGES.get(path.suffix.lower(), "text")


def _resolve(expression: str, source: Path, roots: tuple[Path, ...]) -> Path:
    candidates = [(source.parent / expression).resolve()]
    candidates.extend((root / expression).resolve() for root in roots)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    rendered = ", ".join(str(candidate) for candidate in candidates)
    raise DocsPipelineError(f"Include not found in {source}: {expression!r} (tried {rendered})")


def render_markdown(
    content: str,
    source: Path,
    roots: tuple[Path, ...],
    stack: tuple[Path, ...] = (),
) -> str:
    """Expand include directives recursively while rejecting include cycles."""
    content = _normalise(content)

    def included_body(expression: str) -> tuple[Path, str]:
        target = _resolve(expression.strip(), source, roots)
        if target in stack or target == source:
            chain = " -> ".join(str(path) for path in (*stack, source, target))
            raise DocsPipelineError(f"Cyclic documentation include: {chain}")
        body = _normalise(target.read_text(encoding="utf-8"))
        if target.suffix.lower() in MARKDOWN_SUFFIXES:
            body = render_markdown(body, target, roots, (*stack, source))
        return target, body.rstrip("\n")

    def replace_fenced(match: re.Match[str]) -> str:
        target, body = included_body(match.group("path"))
        language = match.group("language").strip() or _language(target)
        return f"```{language}\n{body}\n```"

    def replace(match: re.Match[str]) -> str:
        target, body = included_body(match.group("path"))
        if target.suffix.lower() in MARKDOWN_SUFFIXES:
            return body
        return f"```{_language(target)}\n{body}\n```"

    rendered = FENCED_INCLUDE.sub(replace_fenced, content)
    rendered = INCLUDE.sub(replace, rendered)
    return rendered.rstrip("\n") + "\n"


def prepare_docs_tree(
    source_dir: Path,
    output_dir: Path,
    *,
    include_roots: tuple[Path, ...],
) -> list[Path]:
    """Create a build tree in a temporary directory and atomically replace the old tree."""
    if not source_dir.is_dir():
        raise DocsPipelineError(f"Documentation source directory not found: {source_dir}")
    temporary = output_dir.parent / f".{output_dir.name}.tmp"
    previous = output_dir.parent / f".{output_dir.name}.previous"
    shutil.rmtree(temporary, ignore_errors=True)
    shutil.rmtree(previous, ignore_errors=True)
    temporary.mkdir(parents=True)
    generated: list[Path] = []
    try:
        for source in sorted(source_dir.rglob("*")):
            if not source.is_file():
                continue
            relative = source.relative_to(source_dir)
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix.lower() in MARKDOWN_SUFFIXES:
                target.write_text(
                    render_markdown(source.read_text(encoding="utf-8"), source, include_roots),
                    encoding="utf-8",
                )
            else:
                shutil.copy2(source, target)
            generated.append(relative)
        if output_dir.exists():
            output_dir.replace(previous)
        try:
            temporary.replace(output_dir)
        except Exception:
            if previous.exists():
                previous.replace(output_dir)
            raise
        shutil.rmtree(previous, ignore_errors=True)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        if previous.exists() and not output_dir.exists():
            previous.replace(output_dir)
        raise
    return [output_dir / relative for relative in generated]


def run_zensical(
    project_root: Path,
    config_file: Path,
    command: str,
    *,
    strict: bool = False,
    clean: bool = False,
    dev_addr: str | None = None,
    open_browser: bool = False,
) -> None:
    """Run one Zensical command against the canonical configuration."""
    arguments = ["zensical", command, "--config-file", str(config_file)]
    if command == "build":
        if clean:
            arguments.append("--clean")
        if strict:
            arguments.append("--strict")
    if command == "serve":
        if dev_addr:
            arguments.extend(("--dev-addr", dev_addr))
        if open_browser:
            arguments.append("--open")
    try:
        subprocess.run(arguments, cwd=project_root, check=True)
    except subprocess.CalledProcessError as exc:
        raise DocsPipelineError(
            f"Zensical failed with exit code {exc.returncode}: {' '.join(arguments)}"
        ) from exc
