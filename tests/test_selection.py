from pathlib import Path

import pytest

from actually.checks import find_violations
from actually.config import SelectionError, load_selection, resolve_selection
from actually.formatting import format_source
from actually.violations import RuleCode

pytestmark = pytest.mark.unit

ALL_CODES: frozenset[RuleCode] = frozenset(
    {
        "ACTC001",
        "ACTC002",
        "ACTC003",
        "ACTC004",
        "ACTL001",
        "ACTL002",
        "ACTR001",
        "ACTR002",
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
            ("ACTC004",),
            ("__ALL__",),
            {
                "ACTC004",
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
            ("ACTC",),
            ("ACTC001",),
            {
                "ACTC002",
                "ACTC003",
                "ACTC004",
            },
            id="specific-exclude-beats-group-include",
        ),
        pytest.param(
            ("ACT",),
            (),
            ALL_CODES,
            id="act-prefix-selects-everything",
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
            ("no-else",),
            (),
            id="rule-name-is-not-a-selector",
        ),
        pytest.param(
            ("ACTC001",),
            ("ACTC001",),
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
            frozenset(
                {
                    "ACTC001",
                }
            ),
        )
    ]

    assert codes == [
        "ACTC001",
    ]


def test_format_skips_fixes_of_disabled_rules() -> None:
    source = "def f(baz):\n    if baz:\n        foo = 42 + 1337\n        return foo\n"

    assert (
        format_source(
            source,
            ALL_CODES
            - {
                "ACTR001",
            },
        )
        == source
    )


def test_format_inserts_comma_without_exploding_when_actl002_disabled() -> None:
    source = 'point = {"x": 1, "y": 2}\n'

    assert format_source(
        source,
        ALL_CODES
        - {
            "ACTL002",
        },
    ) == ('point = {"x": 1, "y": 2,}\n')


@pytest.mark.integration
def test_config_file_lists_are_loaded(tmp_path: Path) -> None:
    (tmp_path / "well-actually.toml").write_text(
        'exclude = ["__ALL__"]\ninclude = ["ACTC004"]\n',
        encoding="utf-8",
    )

    assert load_selection(tmp_path, (), ()) == {
        "ACTC004",
    }


@pytest.mark.integration
def test_config_file_is_discovered_walking_up(tmp_path: Path) -> None:
    (tmp_path / "well-actually.toml").write_text(
        'exclude = ["ACTL"]\n', encoding="utf-8"
    )
    nested = tmp_path / "src" / "pkg"
    nested.mkdir(parents=True)

    assert load_selection(nested, (), ()) == ALL_CODES - {
        "ACTL001",
        "ACTL002",
    }


@pytest.mark.integration
def test_cli_lists_replace_config_lists(tmp_path: Path) -> None:
    (tmp_path / "well-actually.toml").write_text(
        'exclude = ["ACTL"]\n', encoding="utf-8"
    )

    assert load_selection(tmp_path, (), ("ACTR",)) == ALL_CODES - {
        "ACTR001",
        "ACTR002",
    }


@pytest.mark.integration
def test_unknown_config_key_is_a_hard_error(tmp_path: Path) -> None:
    (tmp_path / "well-actually.toml").write_text(
        'select = ["ACTC"]\n', encoding="utf-8"
    )

    with pytest.raises(SelectionError, match="unknown keys"):
        load_selection(tmp_path, (), ())


@pytest.mark.integration
def test_missing_config_file_selects_everything(tmp_path: Path) -> None:
    assert load_selection(tmp_path, (), ()) == ALL_CODES
