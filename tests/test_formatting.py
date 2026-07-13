import pytest

from actually.formatting import format_source


pytestmark = pytest.mark.unit


def test_inserts_blank_line_below_return() -> None:
    source = "def f(foo, bar, baz):\n    if foo:\n        return foo\n    if bar:\n        return baz\n"

    assert format_source(source) == ("def f(foo, bar, baz):\n    if foo:\n        return foo\n\n    if bar:\n        return baz\n")


def test_inserts_blank_line_above_return() -> None:
    source = "def f(baz):\n    if baz:\n        foo = 42 + 1337\n        return foo\n"

    assert format_source(source) == ("def f(baz):\n    if baz:\n        foo = 42 + 1337\n\n        return foo\n")


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "def f():\n    try:\n        value = risky()\n    except ValueError:\n        return 0\n    else:\n        return value\n",
            "def f():\n    try:\n        value = risky()\n    except ValueError:\n        return 0\n\n    return value\n",
            id="every-except-exits-dedents",
        ),
        pytest.param(
            "def f():\n    try:\n        value = risky()\n    except ValueError:\n        value = 0\n    else:\n        log(value)\n",
            "def f():\n    try:\n        value = risky()\n    except ValueError:\n        value = 0\n    else:\n        log(value)\n",
            id="fall-through-except-kept",
        ),
        pytest.param(
            "def f():\n    try:\n        value = risky()\n    except ValueError:\n        raise\n    else:\n        log(value)\n    finally:\n        close()\n",
            "def f():\n    try:\n        value = risky()\n    except ValueError:\n        raise\n    else:\n        log(value)\n    finally:\n        close()\n",
            id="finally-clause-kept",
        ),
        pytest.param(
            'def f():\n    try:\n        value = risky()\n    except ValueError:\n        return 0\n    else:\n        text = """a\nb"""\n        return text\n',
            'def f():\n    try:\n        value = risky()\n    except ValueError:\n        return 0\n\n    text = """a\nb"""\n\n    return text\n',
            id="string-lines-flatter-than-shift-preserved",
        ),
    ],
)
def test_try_else_clause_formatting(source: str, expected: str) -> None:
    assert format_source(source) == expected


def test_if_else_is_reported_not_rewritten() -> None:
    source = "def f(x):\n    if x:\n        return 1\n    else:\n        return 2\n"

    assert format_source(source) == source


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "def f():\n    return 1  # noqa: TID251\n",
            "def f():\n    return 1  # noqa: TID251\n",
            id="trailing-comment-converges",
        ),
        pytest.param(
            "def f(x):\n    if x:\n        return 1  # note\n    y = 2\n",
            "def f(x):\n    if x:\n        return 1  # note\n\n    y = 2\n",
            id="blank-below-lands-past-comment",
        ),
        pytest.param(
            "def f():\n    y = 1; return y\n",
            "def f():\n    y = 1; return y\n",
            id="same-line-preceding-statement-converges",
        ),
        pytest.param(
            "def f():\n    x = 1\n    y = 2; return y\n",
            "def f():\n    x = 1\n\n    y = 2; return y\n",
            id="blank-above-skips-same-line-sibling",
        ),
    ],
)
def test_same_line_sibling_return_spacing(source: str, expected: str) -> None:
    assert format_source(source) == expected


def test_format_is_idempotent() -> None:
    source = "def f(foo, bar, baz):\n    if foo:\n        return foo\n    if bar:\n        return baz\n"

    once = format_source(source)

    assert format_source(once) == once
