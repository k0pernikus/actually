from actually.metadata import FixCapability, RuleCatalog, RuleMetadata
from actually.violations import RuleCode


CHECK_INTRO = "Report violations of the active rule selection without modifying files; exit 1 when any are found."
FORMAT_INTRO = "Rewrite files in place with every auto-fix the active rule selection enables, printing only the files it changes and reporting nothing else; exits 0."
NO_AUTOFIX_NOTICE = "The active selection enables no auto-fixable rule: format rewrites nothing and only reports."
FULL_FIX_HEADER = "Auto-fixed in full:"
PARTIAL_FIX_HEADER = "Auto-fixed where safe, the rest reported:"
CHECK_ONLY_HEADER = "Reported only, never rewritten:"
CHECKED_RULES_HEADER = "Checked rules:"


def check_help(enabled: frozenset[RuleCode], catalog: RuleCatalog, declaration: str) -> str:
    sections = (
        CHECK_INTRO,
        f"\b\n{declaration}",
        _rule_block(CHECKED_RULES_HEADER, _enabled_rules(enabled, catalog)),
    )

    return "\n\n".join(sections)


def format_help(enabled: frozenset[RuleCode], catalog: RuleCatalog, declaration: str) -> str:
    rules = _enabled_rules(enabled, catalog)
    fixable_blocks = _fixable_blocks(rules)
    check_only = _rules_with_fix(rules, "check-only")
    sections = [
        FORMAT_INTRO,
        f"\b\n{declaration}",
    ]
    if not fixable_blocks:
        sections.append(NO_AUTOFIX_NOTICE)

    sections.extend(fixable_blocks)
    if check_only:
        sections.append(_rule_block(CHECK_ONLY_HEADER, check_only))

    return "\n\n".join(sections)


def _fixable_blocks(rules: tuple[RuleMetadata, ...]) -> tuple[str, ...]:
    partitions = (
        (FULL_FIX_HEADER, _rules_with_fix(rules, "full")),
        (PARTIAL_FIX_HEADER, _rules_with_fix(rules, "partial")),
    )

    return tuple(_rule_block(header, members) for header, members in partitions if members)


def _rules_with_fix(rules: tuple[RuleMetadata, ...], fix: FixCapability) -> tuple[RuleMetadata, ...]:
    return tuple(rule for rule in rules if rule.fix == fix)


def _enabled_rules(enabled: frozenset[RuleCode], catalog: RuleCatalog) -> tuple[RuleMetadata, ...]:
    return tuple(sorted((rule for rule in catalog.active if rule.code in enabled), key=_rule_code))


def _rule_code(rule: RuleMetadata) -> str:
    return rule.code


def _rule_block(header: str, rules: tuple[RuleMetadata, ...]) -> str:
    rows = "\n".join(f"  {rule.code} {rule.name}: {rule.summary}" for rule in rules)

    return f"\b\n{header}\n{rows}"
