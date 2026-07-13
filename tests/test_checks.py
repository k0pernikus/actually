import pytest

from actually.checks import find_violations


pytestmark = pytest.mark.unit


def outline(source: str) -> list[tuple[str, int]]:
    return [(violation.rule.code, violation.line) for violation in find_violations(source)]


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "def f(x):\n    if x:\n        return 1\n    else:\n        return 2\n",
            [
                ("ACTC001", 4),
            ],
            id="else-on-if",
        ),
        pytest.param(
            "for i in range(3):\n    use(i)\nelse:\n    done()\n",
            [
                ("ACTC001", 3),
            ],
            id="completion-else-on-for",
        ),
        pytest.param(
            "def f(x):\n    if x == 1:\n        return 1\n    elif x == 2:\n        return 2\n",
            [
                ("ACTC002", 4),
            ],
            id="elif",
        ),
        pytest.param(
            "x = (1 if a else 2) if b else 3\n",
            [
                ("ACTC003", 1),
            ],
            id="nested-ternary",
        ),
        pytest.param(
            "x = [y] if y else []\n",
            [
                ("ACTC004", 1),
                ("ACTL001", 1),
                ("ACTL002", 1),
            ],
            id="empty-list-arm-co-reports-literal-layout",
        ),
    ],
)
def test_banned_conditional_is_flagged(source: str, expected: list[tuple[str, int]]) -> None:
    assert outline(source) == expected


def test_else_on_try_names_the_construct() -> None:
    source = "def f():\n    try:\n        risky()\n    except ValueError:\n        return 0\n    else:\n        return 1\n"

    violations = find_violations(source)

    assert outline(source) == [
        ("ACTC001", 6),
    ]
    assert "`try`" in violations[0].message


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            "x = 1 if condition else 2\n",
            id="flat-ternary",
        ),
        pytest.param(
            'action = "go_to_beach" if sunny else "stay_home"\n',
            id="meaningful-string-arms",
        ),
        pytest.param(
            'x = name if plain else f"{scope}::{short_name}"\n',
            id="inline-literal-separator",
        ),
        pytest.param(
            'x = name if plain else f"{scope}{SCOPE_SEPARATOR}{short_name}"\n',
            id="constant-separator",
        ),
        pytest.param(
            'x = name if plain else f"{scope}{name}"\n',
            id="interpolation-only",
        ),
        pytest.param(
            'x = fallback if missing else f"{name}"\n',
            id="single-placeholder",
        ),
        pytest.param(
            'x = y if c else "\\n"\n',
            id="escape-only-string",
        ),
        pytest.param(
            'SCOPE_SEPARATOR = "::"\n'
            "\n"
            "\n"
            "def _parse_label_def(value: object, scope: str | None, context: str) -> LabelDef:\n"
            "    table = _require_mapping(value, context)\n"
            '    short_name = _require_str(table.get("name"), f"{context}.name")\n'
            '    description = _require_str(table.get("description", ""), f"{context}.description")\n'
            '    name = short_name if scope is None else f"{scope}{SCOPE_SEPARATOR}{short_name}"\n'
            "\n"
            "    return LabelDef(name=name, description=description)\n",
            id="scoped-label-parser-composite",
        ),
    ],
)
def test_valid_ternary_is_clean(source: str) -> None:
    assert outline(source) == []


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            "x = f(y) if y else None\n",
            id="none-arm",
        ),
        pytest.param(
            "parsed = None if raw is None else parse(raw)\n",
            id="none-yielding-assignment",
        ),
        pytest.param(
            'x = y if y else ""\n',
            id="empty-string-arm",
        ),
        pytest.param(
            'x = y if c else f""\n',
            id="empty-fstring-arm",
        ),
    ],
)
def test_degenerate_ternary_arm_is_flagged(source: str) -> None:
    assert outline(source) == [
        ("ACTC004", 1),
    ]


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "def f(foo, bar, baz):\n    if foo:\n        return foo\n    if bar:\n        return baz\n",
            [
                ("ACTR002", 3),
            ],
            id="missing-blank-line-below",
        ),
        pytest.param(
            "def f(baz):\n    if baz:\n        foo = 42 + 1337\n        return foo\n",
            [
                ("ACTR001", 4),
            ],
            id="missing-blank-line-above",
        ),
    ],
)
def test_return_spacing_violation_is_flagged(source: str, expected: list[tuple[str, int]]) -> None:
    assert outline(source) == expected


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            "def f(foo, bar, baz):\n    if foo:\n        return foo\n\n    if bar:\n        return baz\n",
            id="blank-line-below-present",
        ),
        pytest.param(
            "def f(baz):\n    if baz:\n        foo = 42 + 1337\n\n        return foo\n",
            id="blank-line-above-present",
        ),
        pytest.param(
            "def f():\n    return 1\nx = 2\n",
            id="return-ends-function",
        ),
        pytest.param(
            "def f():\n    return 1  # noqa\n",
            id="trailing-comment-on-return",
        ),
        pytest.param(
            "def f():\n    try:\n        return 1\n    except ValueError:\n        raise\n",
            id="return-before-except-clause",
        ),
    ],
)
def test_compliant_return_layout_is_clean(source: str) -> None:
    assert outline(source) == []
