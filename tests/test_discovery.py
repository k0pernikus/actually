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


def test_directory_scan_skips_gitignored_files_without_git_metadata(
    tmp_path: Path,
) -> None:
    (tmp_path / ".gitignore").write_text("generated.py\n")
    (tmp_path / "kept.py").write_text("x = 1\n")
    (tmp_path / "generated.py").write_text("x = 1\n")

    assert python_files((tmp_path,)) == (tmp_path / "kept.py",)


def test_nested_gitignore_applies_only_to_its_own_subtree(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / ".gitignore").write_text("local.py\n")
    (tmp_path / "pkg" / "local.py").write_text("x = 1\n")
    (tmp_path / "local.py").write_text("x = 1\n")

    assert python_files((tmp_path,)) == (tmp_path / "local.py",)


def test_gitignore_negation_reincludes_a_file(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("*.py\n!kept.py\n")
    (tmp_path / "kept.py").write_text("x = 1\n")
    (tmp_path / "dropped.py").write_text("x = 1\n")

    assert python_files((tmp_path,)) == (tmp_path / "kept.py",)


def test_repo_root_gitignore_applies_when_scanning_a_subdirectory(
    tmp_path: Path,
) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("generated.py\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "kept.py").write_text("x = 1\n")
    (tmp_path / "src" / "generated.py").write_text("x = 1\n")

    assert python_files((tmp_path / "src",)) == (tmp_path / "src" / "kept.py",)
