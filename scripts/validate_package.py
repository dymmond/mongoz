"""Build and verify Mongoz distribution artifacts in an isolated environment."""

from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DEFAULT_DATABASE_URI = "mongodb://root:mongoadmin@localhost:27017/?authSource=admin"


def run(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    """Run one package-proof command and preserve its failure."""
    subprocess.run(command, cwd=cwd, env=env, check=True)


def main() -> None:
    """Build, inspect, install, import, and exercise the wheel."""
    build_environment = os.environ.copy()
    build_environment.pop("HATCH_ENV_ACTIVE", None)
    run(["hatch", "build", "--clean"], env=build_environment)

    wheels = sorted(DIST.glob("*.whl"))
    source_distributions = sorted(DIST.glob("*.tar.gz"))
    if len(wheels) != 1 or len(source_distributions) != 1:
        raise RuntimeError(
            f"expected one wheel and one sdist, found {wheels} and {source_distributions}"
        )

    run(["twine", "check", str(wheels[0]), str(source_distributions[0])])

    with tempfile.TemporaryDirectory(prefix="mongoz-wheel-") as temporary_directory:
        isolated_root = Path(temporary_directory)
        environment_root = isolated_root / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment_root)

        if os.name == "nt":
            python = environment_root / "Scripts" / "python.exe"
        else:
            python = environment_root / "bin" / "python"

        clean_environment = os.environ.copy()
        clean_environment.pop("PYTHONPATH", None)
        run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", str(wheels[0])],
            cwd=isolated_root,
            env=clean_environment,
        )
        run([str(python), "-m", "pip", "check"], cwd=isolated_root, env=clean_environment)

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
