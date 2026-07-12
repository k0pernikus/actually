import pytest

from actually.formatting import format_source

pytestmark = pytest.mark.unit


def test_inserts_blank_line_below_return() -> None:
    source = (
        "def f(foo, bar, baz):\n"
        "    if foo:\n"
        "        return foo\n"
        "    if bar:\n"
        "        return baz\n"
    )

    assert format_source(source) == (
        "def f(foo, bar, baz):\n"
        "    if foo:\n"
        "        return foo\n"
        "\n"
        "    if bar:\n"
        "        return baz\n"
    )


def test_inserts_blank_line_above_return() -> None:
    source = "def f(baz):\n    if baz:\n        foo = 42 + 1337\n        return foo\n"

    assert format_source(source) == (
        "def f(baz):\n    if baz:\n        foo = 42 + 1337\n\n        return foo\n"
    )


def test_dedents_try_else_when_every_except_exits() -> None:
    source = (
        "def f():\n"
        "    try:\n"
        "        value = risky()\n"
        "    except ValueError:\n"
        "        return 0\n"
        "    else:\n"
        "        return value\n"
    )

    assert format_source(source) == (
        "def f():\n"
        "    try:\n"
        "        value = risky()\n"
        "    except ValueError:\n"
        "        return 0\n"
        "\n"
        "    return value\n"
    )


def test_try_else_with_fall_through_except_is_not_rewritten() -> None:
    source = (
        "def f():\n"
        "    try:\n"
        "        value = risky()\n"
        "    except ValueError:\n"
        "        value = 0\n"
        "    else:\n"
        "        log(value)\n"
    )

    assert format_source(source) == source


def test_try_else_with_finally_is_not_rewritten() -> None:
    source = (
        "def f():\n"
        "    try:\n"
        "        value = risky()\n"
        "    except ValueError:\n"
        "        raise\n"
        "    else:\n"
        "        log(value)\n"
        "    finally:\n"
        "        close()\n"
    )

    assert format_source(source) == source


def test_if_else_is_reported_not_rewritten() -> None:
    source = "def f(x):\n    if x:\n        return 1\n    else:\n        return 2\n"

    assert format_source(source) == source


def test_dedent_preserves_string_lines_flatter_than_the_shift() -> None:
    source = (
        "def f():\n"
        "    try:\n"
        "        value = risky()\n"
        "    except ValueError:\n"
        "        return 0\n"
        "    else:\n"
        '        text = """a\n'
        'b"""\n'
        "        return text\n"
    )

    assert format_source(source) == (
        "def f():\n"
        "    try:\n"
        "        value = risky()\n"
        "    except ValueError:\n"
        "        return 0\n"
        "\n"
        '    text = """a\n'
        'b"""\n'
        "\n"
        "    return text\n"
    )


def test_trailing_comment_on_return_line_converges() -> None:
    source = "def f():\n    return 1  # noqa: TID251\n"

    assert format_source(source) == source


def test_blank_below_lands_past_a_same_line_comment() -> None:
    source = "def f(x):\n    if x:\n        return 1  # note\n    y = 2\n"

    assert format_source(source) == (
        "def f(x):\n    if x:\n        return 1  # note\n\n    y = 2\n"
    )


def test_same_line_preceding_statement_converges() -> None:
    source = "def f():\n    y = 1; return y\n"

    assert format_source(source) == source


def test_blank_above_skips_same_line_sibling() -> None:
    source = "def f():\n    x = 1\n    y = 2; return y\n"

    assert format_source(source) == ("def f():\n    x = 1\n\n    y = 2; return y\n")


def test_format_is_idempotent() -> None:
    source = (
        "def f(foo, bar, baz):\n"
        "    if foo:\n"
        "        return foo\n"
        "    if bar:\n"
        "        return baz\n"
    )

    once = format_source(source)

    assert format_source(once) == once
