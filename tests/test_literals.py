import pytest

from actually.checks import find_violations
from actually.formatting import format_source

pytestmark = pytest.mark.unit


def outline(source: str) -> list[tuple[str, int]]:
    return [
        (violation.rule.code, violation.line) for violation in find_violations(source)
    ]


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            'point = {"x": 1, "y": 2}\n',
            [
                ("ACTL001", 1),
                ("ACTL002", 1),
            ],
            id="single-line-dict-flags-both-rules",
        ),
        pytest.param(
            'labels = {\n    200: "ok",\n    404: "missing"\n}\n',
            [
                ("ACTL001", 1),
            ],
            id="multiline-missing-only-the-comma",
        ),
        pytest.param(
            'labels = {\n    200: "ok",\n    404: "missing",\n}\n',
            [],
            id="canonical-literal-clean",
        ),
        pytest.param(
            "x = []\ny = {}\n",
            [],
            id="empty-literals-clean",
        ),
        pytest.param(
            "x = (1, 2)\ny = d[str, int]\n",
            [],
            id="tuples-exempt",
        ),
        pytest.param(
            'x = f"{[1, 2]}"\n',
            [],
            id="fstring-interpolation-exempt",
        ),
    ],
)
def test_literal_layout_outline(source: str, expected: list[tuple[str, int]]) -> None:
    assert outline(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            'point = {"x": 1, "y": 2}\n',
            'point = {\n    "x": 1,\n    "y": 2,\n}\n',
            id="explodes-single-line-dict",
        ),
        pytest.param(
            'data = {"a": {"x": 1}, "b": 2}\n',
            'data = {\n    "a": {\n        "x": 1,\n    },\n    "b": 2,\n}\n',
            id="explodes-nested-dict-fully",
        ),
        pytest.param(
            'labels = {\n    200: "ok",\n    404: "missing"\n}\n',
            'labels = {\n    200: "ok",\n    404: "missing",\n}\n',
            id="inserts-only-the-comma",
        ),
        pytest.param(
            'labels = {\n    200: "ok",\n    404: "missing",\n}\n',
            'labels = {\n    200: "ok",\n    404: "missing",\n}\n',
            id="canonical-literal-untouched",
        ),
        pytest.param(
            'x = [foo, """a\nb"""]\n',
            'x = [foo, """a\nb""",]\n',
            id="multiline-element-gets-comma-keeps-layout",
        ),
        pytest.param(
            "merge([1], [2])\n",
            "merge([\n    1,\n], [\n    2,\n])\n",
            id="sibling-literals-both-explode",
        ),
        pytest.param(
            'names = ["solo"]\n',
            'names = [\n    "solo",\n]\n',
            id="single-element-list-explodes",
        ),
    ],
)
def test_literal_layout_formatting(source: str, expected: str) -> None:
    assert format_source(source) == expected
