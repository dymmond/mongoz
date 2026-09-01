from pathlib import Path

import pytest

from scripts.validate_package import DEFAULT_DATABASE_URI, build_smoke_source

pytestmark = pytest.mark.anyio


async def test_installed_wheel_smoke_keeps_database_uri_out_of_process_argv() -> None:
    source = build_smoke_source(Path("/checkout"))
    command = ["python", "-I", "-c", source]
    rendered = " ".join(command)

    assert DEFAULT_DATABASE_URI not in rendered
    assert "root" not in rendered
    assert "mongoadmin" not in rendered
    assert 'os.environ["DATABASE_URI"]' in source
    assert "required_name not in requirement_names" in source
    assert "startswith(required_name)" not in source
