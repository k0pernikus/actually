import contextlib
from pathlib import Path

import pytest
from click.testing import CliRunner

from actually.cli import main
from actually.help_text import (
    CHECK_ONLY_HEADER,
    CHECKED_RULES_HEADER,
    FULL_FIX_HEADER,
    NO_AUTOFIX_NOTICE,
    PARTIAL_FIX_HEADER,
    check_help,
    format_help,
)
from actually.metadata import FixCapability, RuleCatalog, RuleMetadata
from actually.violations import RuleCode, RuleGroup, RuleName


pytestmark = pytest.mark.unit


def _rule(code: RuleCode, name: RuleName, group: RuleGroup, fix: FixCapability, summary: str) -> RuleMetadata:
    return RuleMetadata(
        code=code,
        name=name,
        group=group,
        status="stable",
        fix=fix,
        summary=summary,
        rationale="inert",
        banned="inert",
        wanted="inert",
    )


@pytest.mark.parametrize(
    ("enabled", "present", "absent"),
    [
        pytest.param(
            frozenset({
                "ACTC002",
                "ACTL002",
                "ACTR001",
            }),
            (
                f"{FULL_FIX_HEADER}\n  ACTR001 blank-before-return: a stacked return",
                f"{PARTIAL_FIX_HEADER}\n  ACTL002 one-element-per-line: a crowded literal",
                f"{CHECK_ONLY_HEADER}\n  ACTC002 no-elif: an elif chain",
            ),
            (NO_AUTOFIX_NOTICE,),
            id="full-selection-partitions-by-fix-capability",
        ),
        pytest.param(
            frozenset({
                "ACTR001",
            }),
            (f"{FULL_FIX_HEADER}\n  ACTR001 blank-before-return: a stacked return",),
            (
                "ACTL002",
                "ACTC002",
                PARTIAL_FIX_HEADER,
                CHECK_ONLY_HEADER,
                NO_AUTOFIX_NOTICE,
            ),
            id="disabled-rules-are-never-mentioned",
        ),
        pytest.param(
            frozenset({
                "ACTC002",
            }),
            (
                NO_AUTOFIX_NOTICE,
                f"{CHECK_ONLY_HEADER}\n  ACTC002 no-elif: an elif chain",
            ),
            (
                FULL_FIX_HEADER,
                PARTIAL_FIX_HEADER,
                "ACTR001",
                "ACTL002",
            ),
            id="selection-without-autofix-says-so",
        ),
    ],
)
def test_format_help_names_exactly_the_active_changeset(
    enabled: frozenset[RuleCode],
    present: tuple[str, ...],
    absent: tuple[str, ...],
) -> None:
    catalog = RuleCatalog(
        active=(
            _rule("ACTC002", "no-elif", "actually-conditionals", "check-only", "an elif chain"),
            _rule("ACTL002", "one-element-per-line", "actually-literals", "partial", "a crowded literal"),
            _rule("ACTR001", "blank-before-return", "actually-returns", "full", "a stacked return"),
        ),
        retired=(),
    )

    rendered = format_help(enabled, catalog, "declaration line")

    for fragment in present:
        assert fragment in rendered

    for fragment in absent:
        assert fragment not in rendered


def test_check_help_lists_exactly_the_enabled_rules() -> None:
    catalog = RuleCatalog(
        active=(
            _rule("ACTC002", "no-elif", "actually-conditionals", "check-only", "an elif chain"),
            _rule("ACTL001", "trailing-comma", "actually-literals", "full", "a missing trailing comma"),
        ),
        retired=(),
    )

    rendered = check_help(
        frozenset({
            "ACTC002",
        }),
        catalog,
        "Found well-actually.toml. Running with: ACTC002",
    )

    assert "Found well-actually.toml. Running with: ACTC002" in rendered
    assert f"{CHECKED_RULES_HEADER}\n  ACTC002 no-elif: an elif chain" in rendered
    assert "ACTL001" not in rendered


@pytest.mark.integration
def test_format_help_reflects_the_config_file_selection(tmp_path: Path) -> None:
    (tmp_path / "well-actually.toml").write_text('exclude = ["ACTR"]\n', encoding="utf-8")

    with contextlib.chdir(tmp_path):
        result = (
            (CliRunner())  # well-actually: multi-line
            .invoke(
                main,
                [
                    "format",
                    "--help",
                ],
            )
        )

    assert result.exit_code == 0
    assert "Found well-actually.toml" in result.output
    assert "trailing-comma" in result.output
    assert "blank-before-return" not in result.output


@pytest.mark.integration
def test_help_honors_selection_flags_typed_after_the_help_flag(tmp_path: Path) -> None:
    with contextlib.chdir(tmp_path):
        result = (
            (CliRunner())  # well-actually: multi-line
            .invoke(
                main,
                [
                    "format",
                    "--help",
                    "--exclude",
                    "ACTL",
                ],
            )
        )

    assert result.exit_code == 0
    assert "trailing-comma" not in result.output
    assert "blank-before-return" in result.output


@pytest.mark.integration
def test_check_help_renders_the_selection(tmp_path: Path) -> None:
    with contextlib.chdir(tmp_path):
        result = (
            (CliRunner())  # well-actually: multi-line
            .invoke(
                main,
                [
                    "check",
                    "--help",
                ],
            )
        )

    assert result.exit_code == 0
    assert CHECKED_RULES_HEADER in result.output
    assert "no-elif" in result.output
