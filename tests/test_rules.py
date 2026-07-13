from typing import get_args

import pytest

from actually.violations import RULE_SELECTOR_BY_VALUE, RULES, RuleSelector

pytestmark = pytest.mark.unit


def test_rule_codes_and_names_are_unique() -> None:
    codes = [rule.code for rule in RULES]
    names = [rule.name for rule in RULES]

    assert len(set(codes)) == len(RULES)
    assert len(set(names)) == len(RULES)


def test_selector_vocabulary_matches_the_registry() -> None:
    expected = {
        "__ALL__",
        "ACT",
        *(rule.code for rule in RULES),
        *(rule.code[:-3] for rule in RULES),
    }

    assert set(get_args(RuleSelector)) == expected
    assert set(RULE_SELECTOR_BY_VALUE) == expected
