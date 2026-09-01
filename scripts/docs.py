#!/usr/bin/env python
"""Prepare, build, preview, and clean the Mongoz documentation."""

from __future__ import annotations

import shutil
import threading
from pathlib import Path

import click

try:
    from scripts.docs_pipeline import DocsPipelineError, prepare_docs_tree, run_zensical
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from docs_pipeline import DocsPipelineError, prepare_docs_tree, run_zensical

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "en" / "docs"
SNIPPETS = ROOT / "docs_src"
GENERATED = ROOT / "docs" / "generated"
CONFIG = ROOT / "mkdocs.yaml"
SITE = ROOT / "site"
CACHE = ROOT / ".cache"


def _snapshot(paths: tuple[Path, ...]) -> dict[str, int]:
    state: dict[str, int] = {}
    for path in paths:
        if not path.exists():
            continue
        candidates = (path,) if path.is_file() else sorted(path.rglob("*"))
        for candidate in candidates:
            if candidate.is_file():
                state[str(candidate.resolve())] = candidate.stat().st_mtime_ns
    return state


def _prepare() -> list[Path]:
    generated = prepare_docs_tree(SOURCE, GENERATED, include_roots=(ROOT, SOURCE))
    click.echo(f"Prepared {len(generated)} documentation files in {GENERATED}")
    return generated


def _watch(stop: threading.Event, interval: float = 0.5) -> None:
    paths = (SOURCE, SNIPPETS)
    previous = _snapshot(paths)
    while not stop.wait(interval):
        current = _snapshot(paths)
        if current == previous:
            continue
        previous = current
        try:
            _prepare()
            click.echo("Documentation sources refreshed")
        except DocsPipelineError as exc:
            click.echo(f"Documentation refresh failed: {exc}", err=True)


@click.group()
def cli() -> None:
    """Own the Mongoz documentation build lifecycle."""


@cli.command()
def prepare() -> None:
    """Expand includes into the ephemeral build tree."""
    _prepare()


@cli.command()
def clean() -> None:
    """Remove generated documentation, site output, and Zensical cache."""
    for path in (GENERATED, SITE, CACHE):
        shutil.rmtree(path, ignore_errors=True)
    click.echo("Removed documentation build artifacts")


@cli.command()
@click.option("--clean-cache", is_flag=True, help="Discard the Zensical cache before building.")
def build(clean_cache: bool) -> None:
    """Prepare sources and perform a strict Zensical build."""
    _prepare()
    run_zensical(ROOT, CONFIG, "build", strict=True, clean=clean_cache)


@cli.command()
@click.option("-p", "--port", default=8000, show_default=True, type=int)
@click.option("--open-browser", is_flag=True, help="Open the preview in the default browser.")
@click.option("--watch/--no-watch", default=True, help="Regenerate includes when sources change.")
def serve(port: int, open_browser: bool, watch: bool) -> None:
    """Prepare and preview the site with source and snippet watching."""
    _prepare()
    stop = threading.Event()
    watcher: threading.Thread | None = None
    if watch:
        watcher = threading.Thread(target=_watch, args=(stop,), daemon=True)
        watcher.start()
        click.echo(f"Watching {SOURCE} and {SNIPPETS}")
    try:
        run_zensical(
            ROOT,
            CONFIG,
            "serve",
            dev_addr=f"127.0.0.1:{port}",
            open_browser=open_browser,
        )
    finally:
        stop.set()
        if watcher is not None:
            watcher.join(timeout=1)


if __name__ == "__main__":
    try:
        cli()
    except DocsPipelineError as exc:
        raise click.ClickException(str(exc)) from exc
