from pathlib import Path

import pytest

from actually.discovery import python_files

pytestmark = pytest.mark.integration


def test_directory_scan_skips_venv(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "keep.py").write_text("x = 1\n")
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "swept.py").write_text("x = 1\n")

    assert python_files((tmp_path,)) == (tmp_path / "src" / "keep.py",)


def test_directory_scan_includes_only_python_files(tmp_path: Path) -> None:
    (tmp_path / "keep.py").write_text("x = 1\n")
    (tmp_path / "notes.md").write_text("prose\n")
    (tmp_path / "data.json").write_text("{}\n")

    assert python_files((tmp_path,)) == (tmp_path / "keep.py",)


def test_explicit_non_python_file_is_excluded(tmp_path: Path) -> None:
    prose = tmp_path / "notes.md"
    prose.write_text("prose\n")
    code = tmp_path / "keep.py"
    code.write_text("x = 1\n")

    assert python_files((prose, code)) == (code,)


def test_explicit_python_file_inside_excluded_directory_is_included(
    tmp_path: Path,
) -> None:
    hidden = tmp_path / ".venv" / "tool.py"
    hidden.parent.mkdir(parents=True)
    hidden.write_text("x = 1\n")

    assert python_files((hidden,)) == (hidden,)
