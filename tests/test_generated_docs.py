import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_generated_docs_are_fresh() -> None:
    completed = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_docs.py",
            "--check",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_generator_leaves_outputs_readonly() -> None:
    before = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    completed = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/generate_docs.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (REPO_ROOT / "README.md").read_text(encoding="utf-8") == before
    for output in [
        REPO_ROOT / "README.md",
        *sorted((REPO_ROOT / "rules").glob("*.md")),
    ]:
        assert output.stat().st_mode & 0o222 == 0, f"{output} is writable"
