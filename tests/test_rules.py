import pytest

from actually.metadata import load_rule_catalog, rule_docs_url
from actually.violations import RULE_GROUP_BY_PREFIX, RULE_SELECTOR_BY_VALUE, RULES


pytestmark = pytest.mark.unit


def test_rule_docs_url_is_the_github_page() -> None:
    assert rule_docs_url("no-if-else") == ("https://github.com/k0pernikus/actually/blob/main/rules/no-if-else.md")


@pytest.mark.integration
def test_packaged_catalog_matches_the_registry() -> None:
    catalog = load_rule_catalog()

    assert {rule.code for rule in catalog.active} == {rule.code for rule in RULES}
    assert catalog.retired == ()


def test_rule_codes_and_names_are_unique() -> None:
    codes = [rule.code for rule in RULES]
    names = [rule.name for rule in RULES]

    assert len(set(codes)) == len(RULES)
    assert len(set(names)) == len(RULES)


def test_selector_vocabulary_matches_the_registry() -> None:
    expected = {
        "__ALL__",
        *(rule.code for rule in RULES),
        *(rule.code[:-3] for rule in RULES),
    }

    assert set(RULE_SELECTOR_BY_VALUE) == expected


def test_group_prefixes_map_to_registry_groups() -> None:
    assert set(RULE_GROUP_BY_PREFIX) == {rule.code[:-3] for rule in RULES}
    for rule in RULES:
        assert RULE_GROUP_BY_PREFIX[rule.code[:-3]] == rule.group
