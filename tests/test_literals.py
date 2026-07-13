import pytest

from actually.checks import find_violations
from actually.formatting import format_source

pytestmark = pytest.mark.unit


def outline(source: str) -> list[tuple[str, int]]:
    return [
        (violation.rule.code, violation.line) for violation in find_violations(source)
    ]


def test_single_line_dict_flags_both_rules() -> None:
    assert outline('point = {"x": 1, "y": 2}\n') == [
        ("ACTL001", 1),
        ("ACTL002", 1),
    ]


def test_multiline_literal_missing_only_the_comma() -> None:
    source = 'labels = {\n    200: "ok",\n    404: "missing"\n}\n'

    assert outline(source) == [
        ("ACTL001", 1),
    ]


def test_canonical_literal_is_clean() -> None:
    assert outline('labels = {\n    200: "ok",\n    404: "missing",\n}\n') == []


def test_empty_literal_is_clean() -> None:
    assert outline("x = []\ny = {}\n") == []


def test_tuple_is_exempt() -> None:
    assert outline("x = (1, 2)\ny = d[str, int]\n") == []


def test_literal_inside_fstring_interpolation_is_exempt() -> None:
    assert outline('x = f"{[1, 2]}"\n') == []


def test_explodes_single_line_dict() -> None:
    assert format_source('point = {"x": 1, "y": 2}\n') == (
        'point = {\n    "x": 1,\n    "y": 2,\n}\n'
    )


def test_explodes_nested_dict_to_full_canonical_form() -> None:
    source = 'data = {"a": {"x": 1}, "b": 2}\n'

    assert format_source(source) == (
        'data = {\n    "a": {\n        "x": 1,\n    },\n    "b": 2,\n}\n'
    )


def test_inserts_only_the_comma_into_multiline_literal() -> None:
    source = 'labels = {\n    200: "ok",\n    404: "missing"\n}\n'

    assert format_source(source) == (
        'labels = {\n    200: "ok",\n    404: "missing",\n}\n'
    )


def test_canonical_literal_is_idempotent() -> None:
    source = 'labels = {\n    200: "ok",\n    404: "missing",\n}\n'

    assert format_source(source) == source


def test_literal_with_multiline_element_gets_comma_but_keeps_layout() -> None:
    source = 'x = [foo, """a\nb"""]\n'

    assert format_source(source) == ('x = [foo, """a\nb""",]\n')


def test_sibling_literals_in_one_call_both_explode() -> None:
    source = "merge([1], [2])\n"

    assert format_source(source) == ("merge([\n    1,\n], [\n    2,\n])\n")


def test_single_element_list_explodes() -> None:
    assert format_source('names = ["solo"]\n') == ('names = [\n    "solo",\n]\n')
