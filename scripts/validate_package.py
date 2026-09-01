"""Build and verify Mongoz distribution artifacts in an isolated environment."""

from __future__ import annotations

import os
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


def main() -> None:
    """Build, inspect, install, import, and exercise the wheel."""
    ty_requirement = get_ty_requirement()
    build_environment = os.environ.copy()
    build_environment.pop("HATCH_ENV_ACTIVE", None)
    run(["hatch", "build", "--clean"], env=build_environment)

    wheels = sorted(DIST.glob("*.whl"))
    source_distributions = sorted(DIST.glob("*.tar.gz"))
    if len(wheels) != 1 or len(source_distributions) != 1:
        raise RuntimeError(
            f"expected one wheel and one sdist, found {wheels} and {source_distributions}"
        )

    with zipfile.ZipFile(wheels[0]) as wheel_archive:
        marker = wheel_archive.read("mongoz/py.typed")
        if marker.strip():
            raise RuntimeError("wheel mongoz/py.typed marker must contain only whitespace")

    with tarfile.open(source_distributions[0], "r:gz") as source_archive:
        marker_names = [
            name for name in source_archive.getnames() if name.endswith("/mongoz/py.typed")
        ]
        if len(marker_names) != 1:
            raise RuntimeError(f"expected one sdist py.typed marker, found {marker_names}")
        marker_file = source_archive.extractfile(marker_names[0])
        if marker_file is None or marker_file.read().strip():
            raise RuntimeError("sdist mongoz/py.typed marker must contain only whitespace")

    run(["twine", "check", str(wheels[0]), str(source_distributions[0])])

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
        run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", str(wheels[0])],
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

        smoke = textwrap.dedent(
            f"""
            import asyncio
            from importlib.metadata import version
            from pathlib import Path

            import mongoz

            checkout = Path({str(ROOT)!r}).resolve()
            imported = Path(mongoz.__file__).resolve()
            if imported == checkout or checkout in imported.parents:
                raise RuntimeError(f"wheel smoke imported checkout source: {{imported}}")
            if version("mongoz") != mongoz.__version__:
                raise RuntimeError(
                    f"version mismatch: metadata={{version('mongoz')}} module={{mongoz.__version__}}"
                )

            async def smoke() -> None:
                registry = mongoz.Registry({os.environ.get("DATABASE_URI", DEFAULT_DATABASE_URI)!r})
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
            ],
            cwd=isolated_root,
            env=clean_environment,
        )
        run([str(python), "-m", "pip", "check"], cwd=isolated_root, env=clean_environment)
        floor_smoke = smoke + textwrap.dedent(
            """
            if version("pymongo") != "4.13.0":
                raise RuntimeError(f"PyMongo floor mismatch: {version('pymongo')}")
            """
        )
        run(
            [str(python), "-I", "-c", floor_smoke],
            cwd=isolated_root,
            env=clean_environment,
        )


if __name__ == "__main__":
    main()
