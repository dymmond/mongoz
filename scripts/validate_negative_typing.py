"""Verify that intentional negative consumer fixtures fail for their exact reasons."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "typing" / "negative"
EXPECTED_RULES = {
    "constructor_inference.py": ["invalid-assignment"],
    "field_assignment.py": ["invalid-assignment"],
    "projection_fields.py": ["invalid-argument-type"],
    "query_result.py": ["invalid-assignment"],
    "registry_url.py": ["invalid-argument-type"],
    "session_binding.py": ["invalid-argument-type"],
}


def main() -> None:
    """Require each negative fixture to emit exactly its declared ty rules."""
    failures: list[str] = []
    for name, expected_rules in EXPECTED_RULES.items():
        fixture = FIXTURES / name
        result = subprocess.run(
            ["ty", "check", str(fixture), "--output-format", "concise"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        actual_rules = re.findall(r"error\[([^]]+)]", output)
        if result.returncode == 0:
            failures.append(f"{name}: ty unexpectedly accepted the fixture")
        elif actual_rules != expected_rules:
            failures.append(
                f"{name}: expected rules {expected_rules}, got {actual_rules}\n{output}"
            )

    if failures:
        raise RuntimeError("\n\n".join(failures))

    print(f"Validated {len(EXPECTED_RULES)} intentional negative typing fixtures.")


if __name__ == "__main__":
    main()
