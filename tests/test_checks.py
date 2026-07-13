import pytest

from actually.checks import find_violations

pytestmark = pytest.mark.unit


def outline(source: str) -> list[tuple[str, int]]:
    return [
        (violation.rule.code, violation.line) for violation in find_violations(source)
    ]


def test_else_on_if_is_flagged() -> None:
    source = "def f(x):\n    if x:\n        return 1\n    else:\n        return 2\n"

    assert outline(source) == [
        ("ACTC001", 4),
    ]


def test_else_on_try_names_the_construct() -> None:
    source = (
        "def f():\n"
        "    try:\n"
        "        risky()\n"
        "    except ValueError:\n"
        "        return 0\n"
        "    else:\n"
        "        return 1\n"
    )

    violations = find_violations(source)

    assert outline(source) == [
        ("ACTC001", 6),
    ]
    assert "`try`" in violations[0].message


def test_completion_else_on_for_is_flagged() -> None:
    source = "for i in range(3):\n    use(i)\nelse:\n    done()\n"

    assert outline(source) == [
        ("ACTC001", 3),
    ]


def test_elif_is_flagged() -> None:
    source = (
        "def f(x):\n"
        "    if x == 1:\n"
        "        return 1\n"
        "    elif x == 2:\n"
        "        return 2\n"
    )

    assert outline(source) == [
        ("ACTC002", 4),
    ]


def test_flat_ternary_is_clean() -> None:
    assert outline("x = 1 if condition else 2\n") == []


def test_nested_ternary_is_flagged() -> None:
    assert outline("x = (1 if a else 2) if b else 3\n") == [
        ("ACTC003", 1),
    ]


def test_ternary_with_none_arm_is_flagged() -> None:
    assert outline("x = f(y) if y else None\n") == [
        ("ACTC004", 1),
    ]


def test_none_yielding_assignment_ternary_is_flagged() -> None:
    assert outline("parsed = None if raw is None else parse(raw)\n") == [
        ("ACTC004", 1),
    ]


def test_ternary_with_empty_list_arm_is_flagged() -> None:
    assert outline("x = [y] if y else []\n") == [
        ("ACTC004", 1),
        ("ACTL001", 1),
        ("ACTL002", 1),
    ]


def test_ternary_with_empty_string_arm_is_flagged() -> None:
    assert outline('x = y if y else ""\n') == [
        ("ACTC004", 1),
    ]


def test_ternary_with_two_meaningful_arms_is_clean() -> None:
    assert outline('action = "go_to_beach" if sunny else "stay_home"\n') == []


def test_interpolation_only_fstring_arm_is_not_degenerate() -> None:
    assert outline('x = name if plain else f"{scope}{name}"\n') == []


def test_single_interpolation_fstring_arm_is_not_degenerate() -> None:
    assert outline('x = fallback if missing else f"{name}"\n') == []


def test_empty_fstring_arm_is_degenerate() -> None:
    assert outline('x = y if c else f""\n') == [
        ("ACTC004", 1),
    ]


def test_escape_only_string_arm_is_not_degenerate() -> None:
    assert outline('x = y if c else "\\n"\n') == []


def test_scoped_label_parser_shape_is_clean() -> None:
    source = (
        'SCOPE_SEPARATOR = "::"\n'
        "\n"
        "\n"
        "def _parse_label_def(value: object, scope: str | None, context: str) -> LabelDef:\n"
        "    table = _require_mapping(value, context)\n"
        '    short_name = _require_str(table.get("name"), f"{context}.name")\n'
        '    description = _require_str(table.get("description", ""), f"{context}.description")\n'
        '    name = short_name if scope is None else f"{scope}{SCOPE_SEPARATOR}{short_name}"\n'
        "\n"
        "    return LabelDef(name=name, description=description)\n"
    )

    assert outline(source) == []


def test_return_needs_blank_line_below_when_code_follows() -> None:
    source = (
        "def f(foo, bar, baz):\n"
        "    if foo:\n"
        "        return foo\n"
        "    if bar:\n"
        "        return baz\n"
    )

    assert outline(source) == [
        ("ACTR002", 3),
    ]


def test_return_with_blank_line_below_is_clean() -> None:
    source = (
        "def f(foo, bar, baz):\n"
        "    if foo:\n"
        "        return foo\n"
        "\n"
        "    if bar:\n"
        "        return baz\n"
    )

    assert outline(source) == []


def test_return_needs_blank_line_above_in_larger_block() -> None:
    source = "def f(baz):\n    if baz:\n        foo = 42 + 1337\n        return foo\n"

    assert outline(source) == [
        ("ACTR001", 4),
    ]


def test_return_with_blank_line_above_is_clean() -> None:
    source = "def f(baz):\n    if baz:\n        foo = 42 + 1337\n\n        return foo\n"

    assert outline(source) == []


def test_return_ending_a_function_needs_no_blank_below() -> None:
    source = "def f():\n    return 1\nx = 2\n"

    assert outline(source) == []


def test_trailing_comment_on_return_line_is_clean() -> None:
    assert outline("def f():\n    return 1  # noqa\n") == []


def test_return_directly_before_except_clause_is_exempt() -> None:
    source = (
        "def f():\n    try:\n        return 1\n    except ValueError:\n        raise\n"
    )

    assert outline(source) == []
