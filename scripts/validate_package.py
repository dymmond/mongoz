"""Build and verify Mongoz distribution artifacts in isolated environments."""

from __future__ import annotations

import argparse
import ast
import email.parser
import os
import re
import subprocess
import tarfile
import tempfile
import textwrap
import venv
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 packaging validation
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DEFAULT_DATABASE_URI = "mongodb://root:mongoadmin@localhost:27017/?authSource=admin"
BANNED_ARCHIVE_PARTS = {
    ".cache",
    ".git",
    ".github",
    ".pytest_cache",
    "AGENTS.md",
    "__pycache__",
    "coverage.json",
    "coverage.xml",
    "docs/generated",
    "results",
    "site",
}


def canonical_version() -> str:
    """Read the canonical version without importing the checkout."""
    source = ROOT / "mongoz" / "__init__.py"
    module = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    values = [
        node.value.value
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        )
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    if len(values) != 1:
        raise RuntimeError(f"expected one literal __version__ in {source}")
    return values[0]


def get_ty_requirement() -> str:
    """Return the canonical ty requirement from the project quality dependencies."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    quality_dependencies = project["project"]["optional-dependencies"]["quality"]
    requirements = [item for item in quality_dependencies if item.startswith("ty==")]
    if len(requirements) != 1:
        raise RuntimeError(f"expected one pinned ty quality dependency, found {requirements}")
    return requirements[0]


def run(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    """Run one package-proof command and preserve its failure."""
    subprocess.run(command, cwd=cwd, env=env, check=True)


def artifact_pair() -> tuple[Path, Path]:
    """Return the sole wheel and source distribution for the canonical version."""
    version = canonical_version()
    wheels = sorted(DIST.glob("*.whl"))
    source_distributions = sorted(DIST.glob("*.tar.gz"))
    expected_wheel = f"mongoz-{version}-py3-none-any.whl"
    expected_sdist = f"mongoz-{version}.tar.gz"
    if [path.name for path in wheels] != [expected_wheel]:
        raise RuntimeError(f"expected only {expected_wheel}, found {wheels}")
    if [path.name for path in source_distributions] != [expected_sdist]:
        raise RuntimeError(f"expected only {expected_sdist}, found {source_distributions}")
    return wheels[0], source_distributions[0]


def assert_safe_members(names: list[str], *, archive: Path) -> None:
    """Reject traversal, generated output, credentials, and campaign material."""
    failures: list[str] = []
    for name in names:
        normalized = name.replace("\\", "/")
        if normalized.startswith("/") or "../" in f"/{normalized}/":
            failures.append(name)
            continue
        components = set(normalized.split("/"))
        if any(
            (part in components if "/" not in part else f"/{part}/" in f"/{normalized}/")
            for part in BANNED_ARCHIVE_PARTS
        ):
            failures.append(name)
    if failures:
        raise RuntimeError(f"unsafe or unwanted members in {archive.name}: {failures}")


def validate_metadata(raw: bytes, *, version: str, source: str) -> None:
    """Validate core metadata projected from pyproject and the version owner."""
    metadata = email.parser.BytesParser().parsebytes(raw)
    expected = {
        "Name": "mongoz",
        "Version": version,
        "Summary": "Typed asynchronous MongoDB documents and queries for Python.",
        "Requires-Python": ">=3.10",
        "License-Expression": "BSD-3-Clause",
    }
    mismatches = {
        key: (metadata.get(key), value)
        for key, value in expected.items()
        if metadata.get(key) != value
    }
    if mismatches:
        raise RuntimeError(f"metadata mismatch in {source}: {mismatches}")
    requirements = metadata.get_all("Requires-Dist") or []
    runtime = [requirement for requirement in requirements if "extra ==" not in requirement]
    requirement_names = [
        match.group(0).lower()
        for requirement in runtime
        if (match := re.match(r"[A-Za-z0-9_.-]+", requirement)) is not None
    ]
    if len(requirement_names) != len(runtime):
        raise RuntimeError(f"invalid runtime requirement in {source}: {runtime}")
    if any(name in {"motor", "orjson"} for name in requirement_names):
        raise RuntimeError(f"removed runtime dependency in {source}: {runtime}")
    actual_runtime = dict(zip(requirement_names, runtime, strict=True))
    expected_runtime = {
        "pydantic": "pydantic<3.0,>=2.10",
        "pydantic-settings": "pydantic-settings<3.0,>=2.9",
        "pymongo": "pymongo<5.0,>=4.13",
    }
    if actual_runtime != expected_runtime:
        raise RuntimeError(
            f"runtime requirements in {source} are {actual_runtime}, expected {expected_runtime}"
        )
    classifiers = set(metadata.get_all("Classifier") or [])
    expected_classifiers = {
        f"Programming Language :: Python :: 3.{minor}" for minor in range(10, 15)
    }
    if not expected_classifiers <= classifiers or "Typing :: Typed" not in classifiers:
        raise RuntimeError(f"Python or typing classifiers incomplete in {source}")
    urls = metadata.get_all("Project-URL") or []
    for label in ("Documentation", "Changelog", "Issues", "Security", "Source"):
        if not any(url.startswith(f"{label}, ") for url in urls):
            raise RuntimeError(f"missing {label} project URL in {source}: {urls}")
    payload = metadata.get_payload()
    if not isinstance(payload, str) or not payload.startswith("# Mongoz"):
        raise RuntimeError(f"README payload missing from {source}")


def validate_wheel(wheel: Path, *, version: str) -> None:
    """Validate wheel metadata, typing marker, license, and manifest exclusions."""
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert_safe_members(names, archive=wheel)
        allowed_roots = {"mongoz", f"mongoz-{version}.dist-info"}
        unexpected = [name for name in names if name.split("/", 1)[0] not in allowed_roots]
        if unexpected:
            raise RuntimeError(f"unexpected wheel members: {unexpected}")
        marker = archive.read("mongoz/py.typed")
        if marker.strip():
            raise RuntimeError("wheel mongoz/py.typed marker must contain only whitespace")
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        license_names = [name for name in names if name.endswith(".dist-info/licenses/LICENSE")]
        if len(metadata_names) != 1 or len(license_names) != 1:
            raise RuntimeError(
                f"wheel metadata/license manifest is incomplete: {metadata_names}, {license_names}"
            )
        validate_metadata(archive.read(metadata_names[0]), version=version, source=wheel.name)


def validate_sdist(source_distribution: Path, *, version: str) -> None:
    """Validate source metadata, required project files, and manifest exclusions."""
    prefix = f"mongoz-{version}/"
    with tarfile.open(source_distribution, "r:gz") as archive:
        names = archive.getnames()
        assert_safe_members(names, archive=source_distribution)
        allowed_roots = {
            prefix + ".gitignore",
            prefix + "LICENSE",
            prefix + "README.md",
            prefix + "pyproject.toml",
            prefix + "PKG-INFO",
        }
        unexpected = [
            name
            for name in names
            if name not in allowed_roots
            and not name.startswith(prefix + "mongoz/")
            and name != prefix.rstrip("/")
        ]
        if unexpected:
            raise RuntimeError(f"unexpected sdist members: {unexpected}")
        required = {
            prefix + ".gitignore",
            prefix + "LICENSE",
            prefix + "README.md",
            prefix + "pyproject.toml",
            prefix + "PKG-INFO",
            prefix + "mongoz/py.typed",
        }
        missing = required - set(names)
        if missing:
            raise RuntimeError(f"sdist manifest is incomplete: {sorted(missing)}")
        marker = archive.extractfile(prefix + "mongoz/py.typed")
        metadata = archive.extractfile(prefix + "PKG-INFO")
        if marker is None or marker.read().strip():
            raise RuntimeError("sdist mongoz/py.typed marker must contain only whitespace")
        if metadata is None:
            raise RuntimeError("sdist PKG-INFO is unreadable")
        validate_metadata(metadata.read(), version=version, source=source_distribution.name)


def rebuild_sdist(source_distribution: Path, *, version: str) -> None:
    """Build a wheel from the accepted sdist in an isolated directory and inspect it."""
    with tempfile.TemporaryDirectory(prefix="mongoz-sdist-") as directory:
        root = Path(directory)
        rebuilt = root / "wheel"
        rebuilt.mkdir()
        clean_environment = os.environ.copy()
        clean_environment.pop("PYTHONPATH", None)
        run(
            [
                os.sys.executable,
                "-m",
                "pip",
                "wheel",
                "--disable-pip-version-check",
                "--no-deps",
                "--wheel-dir",
                str(rebuilt),
                str(source_distribution),
            ],
            cwd=root,
            env=clean_environment,
        )
        wheels = list(rebuilt.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(f"sdist rebuild produced unexpected wheels: {wheels}")
        validate_wheel(wheels[0], version=version)


def build_smoke_source(checkout: Path) -> str:
    """Build credential-independent source for an installed-wheel smoke process."""
    return textwrap.dedent(
        f"""
        import asyncio
        import importlib.util
        import os
        from importlib.metadata import metadata, version
        from pathlib import Path

        import mongoz

        checkout = Path({str(checkout)!r}).resolve()
        imported = Path(mongoz.__file__).resolve()
        if imported == checkout or checkout in imported.parents:
            raise RuntimeError(f"wheel smoke imported checkout source: {{imported}}")
        if version("mongoz") != mongoz.__version__:
            raise RuntimeError(
                f"version mismatch: metadata={{version('mongoz')}} module={{mongoz.__version__}}"
            )
        requirements = metadata("mongoz").get_all("Requires-Dist") or []
        if any(requirement.lower().startswith(("motor", "orjson")) for requirement in requirements):
            raise RuntimeError(f"removed dependency remains: {{requirements}}")
        for removed in ("motor", "orjson"):
            if importlib.util.find_spec(removed) is not None:
                raise RuntimeError(f"removed package unexpectedly installed: {{removed}}")
        for required_name in ("pydantic", "pydantic-settings", "pymongo"):
            if not any(
                requirement.lower().startswith(required_name) for requirement in requirements
            ):
                raise RuntimeError(
                    f"missing direct runtime dependency {{required_name}}: {{requirements}}"
                )

        async def smoke() -> None:
            registry = mongoz.Registry(os.environ["DATABASE_URI"])
            try:
                result = await registry.driver.admin.command("ping")
                if result.get("ok") != 1.0:
                    raise RuntimeError(f"installed-wheel MongoDB ping failed: {{result}}")
            finally:
                await registry.close()

        asyncio.run(smoke())
        print(
            f"Imported installed wheel from {{imported}} "
            f"with PyMongo {{version('pymongo')}}"
        )
        """
    )


def validate_installed_wheel(wheel: Path) -> None:
    """Install the wheel cleanly, prove typing, runtime, and dependency floors."""
    ty_requirement = get_ty_requirement()
    with tempfile.TemporaryDirectory(prefix="mongoz-wheel-") as temporary_directory:
        isolated_root = Path(temporary_directory)
        environment_root = isolated_root / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment_root)

        if os.name == "nt":
            python = environment_root / "Scripts" / "python.exe"
            ty = environment_root / "Scripts" / "ty.exe"
        else:
            python = environment_root / "bin" / "python"
            ty = environment_root / "bin" / "ty"

        clean_environment = os.environ.copy()
        clean_environment.pop("PYTHONPATH", None)
        clean_environment.setdefault("DATABASE_URI", DEFAULT_DATABASE_URI)
        run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", str(wheel)],
            cwd=isolated_root,
            env=clean_environment,
        )
        run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                ty_requirement,
            ],
            cwd=isolated_root,
            env=clean_environment,
        )
        run([str(python), "-m", "pip", "check"], cwd=isolated_root, env=clean_environment)

        typing_consumer = isolated_root / "consumer.py"
        typing_consumer.write_text(
            textwrap.dedent(
                """
                from typing_extensions import assert_type

                import mongoz

                registry = mongoz.Registry("mongodb://localhost:27017")
                database = registry.get_database("wheel_typing")

                class WheelUser(mongoz.Document):
                    name: str = mongoz.String()

                    class Meta:
                        registry = registry
                        database = database

                user = WheelUser(name="Ada")
                assert_type(user, WheelUser)
                assert_type(WheelUser.objects, mongoz.Manager[WheelUser])
                assert_type(WheelUser.query(), mongoz.QuerySet[WheelUser])
                """
            ),
            encoding="utf-8",
        )
        run(
            [str(ty), "check", "--python", str(python), str(typing_consumer)],
            cwd=isolated_root,
            env=clean_environment,
        )

        smoke = build_smoke_source(ROOT)
        run([str(python), "-I", "-c", smoke], cwd=isolated_root, env=clean_environment)

        run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--force-reinstall",
                "pymongo==4.13.0",
                "pydantic==2.10.0",
                "pydantic-settings==2.9.0",
            ],
            cwd=isolated_root,
            env=clean_environment,
        )
        run([str(python), "-m", "pip", "check"], cwd=isolated_root, env=clean_environment)
        floor_smoke = smoke + textwrap.dedent(
            """
            if version("pymongo") != "4.13.0":
                raise RuntimeError(f"PyMongo floor mismatch: {version('pymongo')}")
            if version("pydantic") != "2.10.0":
                raise RuntimeError(f"Pydantic floor mismatch: {version('pydantic')}")
            if version("pydantic-settings") != "2.9.0":
                raise RuntimeError(
                    f"Pydantic Settings floor mismatch: {version('pydantic-settings')}"
                )
            """
        )
        run([str(python), "-I", "-c", floor_smoke], cwd=isolated_root, env=clean_environment)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="validate the existing dist directory without rebuilding release artifacts",
    )
    return parser.parse_args()


def main() -> None:
    """Build once if requested, then inspect and exercise wheel and sdist artifacts."""
    args = parse_args()
    if not args.no_build:
        build_environment = os.environ.copy()
        build_environment.pop("HATCH_ENV_ACTIVE", None)
        run(["hatch", "build", "--clean"], env=build_environment)
    wheel, source_distribution = artifact_pair()
    version = canonical_version()
    validate_wheel(wheel, version=version)
    validate_sdist(source_distribution, version=version)
    run(["twine", "check", str(wheel), str(source_distribution)])
    rebuild_sdist(source_distribution, version=version)
    validate_installed_wheel(wheel)


if __name__ == "__main__":
    main()
