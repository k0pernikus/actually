from pathlib import Path

import pytest

from actually.checks import find_violations
from actually.config import (
    SelectionError,
    describe_selection,
    load_selection,
    resolve_selection,
)
from actually.formatting import format_source
from actually.violations import RuleCode


pytestmark = pytest.mark.unit

ALL_CODES: frozenset[RuleCode] = frozenset(
    {
        "ACTI001",
        "ACTI002",
        "ACTI003",
        "ACTT001",
        "ACTT002",
        "ACTE001",
        "ACTE002",
        "ACTE003",
        "ACTH001",
        "ACTL001",
        "ACTL002",
        "ACTR001",
        "ACTR002",
        "ACTO001",
    },
)


@pytest.mark.parametrize(
    ("include", "exclude", "expected"),
    [
        pytest.param(
            (),
            (),
            ALL_CODES,
            id="defaults-select-everything",
        ),
        pytest.param(
            (),
            ("ACTL",),
            ALL_CODES
            - {
                "ACTL001",
                "ACTL002",
            },
            id="exclude-only-drops-a-group",
        ),
        pytest.param(
            ("ACTT002",),
            ("__ALL__",),
            {
                "ACTT002",
            },
            id="exclude-all-include-one",
        ),
        pytest.param(
            ("ACTR",),
            (),
            {
                "ACTR001",
                "ACTR002",
            },
            id="include-group-drops-the-rest",
        ),
        pytest.param(
            ("__ALL__", "ACTL001"),
            ("ACTL",),
            ALL_CODES
            - {
                "ACTL002",
            },
            id="exclude-group-reinclude-one-member",
        ),
        pytest.param(
            ("ACTI",),
            ("ACTI001",),
            {
                "ACTI002",
                "ACTI003",
            },
            id="specific-exclude-beats-group-include",
        ),
    ],
)
def test_selection_resolves(
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    expected: frozenset[str],
) -> None:
    assert resolve_selection(include, exclude) == expected


@pytest.mark.parametrize(
    ("include", "exclude"),
    [
        pytest.param(
            ("__ALL__",),
            ("__ALL__",),
            id="all-in-both-lists",
        ),
        pytest.param(
            ("__ALL__", "__ALL__"),
            (),
            id="all-twice-in-one-list",
        ),
        pytest.param(
            (),
            ("__ALL__",),
            id="exclude-all-without-include",
        ),
        pytest.param(
            ("ACTX001",),
            (),
            id="unknown-selector",
        ),
        pytest.param(
            ("ACT",),
            (),
            id="bare-act-is-not-a-selector",
        ),
        pytest.param(
            ("no-if-else",),
            (),
            id="rule-name-is-not-a-selector",
        ),
        pytest.param(
            ("ACTI001",),
            ("ACTI001",),
            id="same-selector-in-both-lists",
        ),
        pytest.param(
            ("ACTL", "ACTL"),
            (),
            id="selector-twice-in-one-list",
        ),
        pytest.param(
            ("ACTT",),
            ("ACTT001", "ACTT002"),
            id="selection-enables-nothing",
        ),
    ],
)
def test_invalid_selection_is_a_hard_error(
    include: tuple[str, ...],
    exclude: tuple[str, ...],
) -> None:
    with pytest.raises(SelectionError, match="."):
        resolve_selection(include, exclude)


def test_check_reports_only_enabled_rules() -> None:
    source = "def f(x):\n    if x:\n        y = 1\n        return y\n    else:\n        return 0\n"

    codes = [
        violation.rule.code
        for violation in find_violations(
            source,
            frozenset({
                "ACTI001",
            }),
        )
    ]

    assert codes == [
        "ACTI001",
    ]


@pytest.mark.parametrize(
    ("disabled", "source", "expected"),
    [
        pytest.param(
            "ACTR001",
            "def f(baz):\n    if baz:\n        foo = 42 + 1337\n        return foo\n",
            "def f(baz):\n    if baz:\n        foo = 42 + 1337\n        return foo\n",
            id="blank-line-fix-skipped",
        ),
        pytest.param(
            "ACTL002",
            'point = {"x": 1, "y": 2}\n',
            'point = {"x": 1, "y": 2,}\n',
            id="explosion-skipped-comma-still-lands",
        ),
        pytest.param(
            "ACTH001",
            "value = make(1).build().render()\n",
            "value = make(1).build().render()\n",
            id="chain-explosion-skipped",
        ),
    ],
)
def test_disabled_rule_contributes_no_fixes(disabled: RuleCode, source: str, expected: str) -> None:
    enabled = ALL_CODES - {
        disabled,
    }

    assert format_source(source, enabled) == expected


@pytest.mark.parametrize(
    ("enabled", "expected"),
    [
        pytest.param(
            ALL_CODES,
            "__ALL__",
            id="everything-is-the-all-group",
        ),
        pytest.param(
            ALL_CODES
            - {
                "ACTL001",
                "ACTL002",
            },
            "__ALL__ except ACTL001, ACTL002",
            id="minority-exclusion-renders-as-except",
        ),
        pytest.param(
            frozenset({
                "ACTT002",
            }),
            "ACTT002",
            id="minority-inclusion-renders-as-list",
        ),
    ],
)
def test_selection_description(enabled: frozenset[RuleCode], expected: str) -> None:
    assert describe_selection(enabled) == expected


@pytest.mark.integration
def test_config_file_lists_are_loaded(tmp_path: Path) -> None:
    (tmp_path / "well-actually.toml").write_text(
        'exclude = ["__ALL__"]\ninclude = ["ACTT002"]\n',
        encoding="utf-8",
    )

    loaded = load_selection(tmp_path, (), ())

    assert loaded.enabled == {
        "ACTT002",
    }
    assert loaded.config_file_found


@pytest.mark.integration
def test_parent_directory_config_is_not_sourced(tmp_path: Path) -> None:
    (tmp_path / "well-actually.toml").write_text('exclude = ["ACTL"]\n', encoding="utf-8")
    nested = tmp_path / "src" / "pkg"
    nested.mkdir(parents=True)

    loaded = load_selection(nested, (), ())

    assert loaded.enabled == ALL_CODES
    assert not loaded.config_file_found


@pytest.mark.integration
def test_cli_lists_replace_config_lists(tmp_path: Path) -> None:
    (tmp_path / "well-actually.toml").write_text('exclude = ["ACTL"]\n', encoding="utf-8")

    assert load_selection(tmp_path, (), ("ACTR",)).enabled == ALL_CODES - {
        "ACTR001",
        "ACTR002",
    }


@pytest.mark.integration
def test_unknown_config_key_is_a_hard_error(tmp_path: Path) -> None:
    (tmp_path / "well-actually.toml").write_text('select = ["ACTI"]\n', encoding="utf-8")

    with pytest.raises(SelectionError, match="unknown keys"):
        load_selection(tmp_path, (), ())


@pytest.mark.integration
def test_missing_config_file_selects_everything(tmp_path: Path) -> None:
    loaded = load_selection(tmp_path, (), ())

    assert loaded.enabled == ALL_CODES
    assert not loaded.config_file_found
