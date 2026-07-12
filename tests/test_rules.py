import pytest

from actually.violations import RULES

pytestmark = pytest.mark.unit


def test_rule_codes_and_names_are_unique() -> None:
    codes = [rule.code for rule in RULES]
    names = [rule.name for rule in RULES]

    assert len(set(codes)) == len(RULES)
    assert len(set(names)) == len(RULES)
