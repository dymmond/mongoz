from pathlib import Path

import pytest

from scripts.validate_package import build_smoke_source

pytestmark = pytest.mark.anyio


async def test_installed_wheel_smoke_keeps_database_uri_out_of_process_argv() -> None:
    credential_uri = "mongodb://manifest-user:manifest-password@db.example/mongoz"
    source = build_smoke_source(Path("/checkout"))
    command = ["python", "-I", "-c", source]

    assert credential_uri not in " ".join(command)
    assert "manifest-user" not in " ".join(command)
    assert "manifest-password" not in " ".join(command)
    assert 'os.environ["DATABASE_URI"]' in source
