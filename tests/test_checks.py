import pytest

from actually.checks import find_violations

pytestmark = pytest.mark.unit


def outline(source: str) -> list[tuple[str, int]]:
    return [(violation.rule, violation.line) for violation in find_violations(source)]


def test_else_on_if_is_flagged() -> None:
    source = "def f(x):\n    if x:\n        return 1\n    else:\n        return 2\n"

    assert outline(source) == [("no-else", 4)]


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

    assert outline(source) == [("no-else", 6)]
    assert "`try`" in violations[0].message


def test_completion_else_on_for_is_flagged() -> None:
    source = "for i in range(3):\n    use(i)\nelse:\n    done()\n"

    assert outline(source) == [("no-else", 3)]


def test_elif_is_flagged() -> None:
    source = (
        "def f(x):\n"
        "    if x == 1:\n"
        "        return 1\n"
        "    elif x == 2:\n"
        "        return 2\n"
    )

    assert outline(source) == [("no-elif", 4)]


def test_flat_ternary_is_clean() -> None:
    assert outline("x = 1 if condition else 2\n") == []


def test_nested_ternary_is_flagged() -> None:
    assert outline("x = (1 if a else 2) if b else 3\n") == [("no-nested-ternary", 1)]


def test_return_needs_blank_line_below_when_code_follows() -> None:
    source = (
        "def f(foo, bar, baz):\n"
        "    if foo:\n"
        "        return foo\n"
        "    if bar:\n"
        "        return baz\n"
    )

    assert outline(source) == [("blank-after-return", 3)]


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

    assert outline(source) == [("blank-before-return", 4)]


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
