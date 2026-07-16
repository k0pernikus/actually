import contextlib
from importlib.metadata import version
from pathlib import Path

import pytest
from click.testing import CliRunner

from actually.cli import main


pytestmark = pytest.mark.integration


REPORTED_ONLY = "value = (\n    obj  # keep\n    .a()\n    .b()\n)\n"

MIXED = "value = obj.a().b()\ndetail = (\n    other  # keep\n    .c()\n    .d()\n)\nif x == 1:\n    result = 1\nelif x == 2:\n    result = 2\n"


def _invoke(tmp_path: Path, source: str, args: list[str]) -> tuple[int, str, str]:
    target = tmp_path / "m.py"
    target.write_text(source, encoding="utf-8")
    with contextlib.chdir(tmp_path):
        result = (CliRunner()).invoke(
            main,
            [
                *args,
                str(target),
            ],
        )

    return result.exit_code, result.output, target.read_text(encoding="utf-8")


def test_format_is_silent_when_it_changes_nothing(tmp_path: Path) -> None:
    exit_code, output, after = _invoke(
        tmp_path,
        REPORTED_ONLY,
        [
            "format",
        ],
    )

    assert exit_code == 0
    assert output == ""
    assert after == REPORTED_ONLY


def test_format_applies_fixes_without_reporting_the_remainder(tmp_path: Path) -> None:
    exit_code, output, after = _invoke(
        tmp_path,
        MIXED,
        [
            "format",
        ],
    )

    assert exit_code == 0
    assert "ACTH001" not in output
    assert "# well-actually: multi-line" in after
    assert "other  # keep" in after


def test_check_only_autofixable_reports_the_mechanical_set(tmp_path: Path) -> None:
    exit_code, output, _after = _invoke(
        tmp_path,
        MIXED,
        [
            "check",
            "--only-autofixable",
        ],
    )

    assert exit_code == 1
    assert ":1 ACTH001" in output
    assert ":3 ACTH001" not in output
    assert "ACTI002" not in output


def test_check_ignore_autofixable_reports_the_manual_set(tmp_path: Path) -> None:
    exit_code, output, _after = _invoke(
        tmp_path,
        MIXED,
        [
            "check",
            "--ignore-autofixable",
        ],
    )

    assert exit_code == 1
    assert ":1 ACTH001" not in output
    assert ":3 ACTH001" in output
    assert "ACTI002" in output


def test_check_rejects_both_autofixable_filters(tmp_path: Path) -> None:
    exit_code, _output, _after = _invoke(
        tmp_path,
        MIXED,
        [
            "check",
            "--only-autofixable",
            "--ignore-autofixable",
        ],
    )

    assert exit_code == 2


def test_version_flag_renders_the_banner_and_current_version() -> None:
    result = (CliRunner()).invoke(
        main,
        [
            "--version",
        ],
    )

    assert result.exit_code == 0
    assert version("well-actually") in result.output
