"""Canonical release metadata readers shared by release tooling."""

from __future__ import annotations

import ast
import re
from pathlib import Path

VERSION_PATTERN = re.compile(r"0\.\d+\.\d+(?:rc(?:0|[1-9]\d*))?\Z")


def read_canonical_version(source: Path) -> str:
    """Read and validate the sole literal package version assignment."""
    module = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    assignments = [
        node.value.value
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        )
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    if len(assignments) != 1:
        raise RuntimeError(f"expected one literal __version__ in {source}")
    version = assignments[0]
    if not VERSION_PATTERN.fullmatch(version):
        raise RuntimeError(
            f"canonical version {version!r} must follow 0.MINOR.PATCH or 0.MINOR.PATCHrcN"
        )
    return version
