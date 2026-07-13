# 6 — Selector Taxonomy: Rule, Group, All-Group

**Status:** Accepted
**Created:** 2026-07-13
**Updated:** 2026-07-13
**See also:** [ADR 1](1_ruff_style_rule_codes_in_named_groups.md), [ADR 5](5_rule_selection_by_prefix_specificity.md)

## Context

- the first selection implementation flattened every valid selector string into one hand-written
  `Literal`, mixing three different kinds of thing — and admitted bare `ACT` as a second
  spelling for "everything"
- a selector is not one kind: `ACTL001` names a **rule**, `ACTL` names the **group** the rule
  belongs to, and `__ALL__` names the whole rule set

## Decision

The taxonomy is three taxa, each its own type, composed by union — never a flat enumeration:

| Taxon | Type | Identified by | Example |
|:---|:---|:---|:---|
| rule | `RuleCode` | code | `ACTL001` |
| group | `RuleGroupPrefix` | code prefix (letter allocated in ADR 1) | `ACTL` |
| all-group | `AllGroup` | the `__ALL__` sentinel | `__ALL__` |

- `RuleSelector = AllGroup | RuleGroupPrefix | RuleCode` — the union IS the statement that a
  selector is exactly one of the three
- `__ALL__` is a special all-encompassing rule group, not a magic string: it selects every rule
  at the lowest specificity
- bare `ACT` is NOT a selector: with `__ALL__` as the everything-group it was a redundant second
  spelling, and redundant spellings are authoring mistakes to reject, not tolerate
- a group has two representations with one owner each: the prefix (`ACTL`, selection vocabulary)
  and the display name (`actually-literals`, docs and `Rule.group`); `RULE_GROUP_BY_PREFIX`
  anchors the correspondence and tests pin it against the registry

## Consequences

- the boundary lookup (`RULE_SELECTOR_BY_VALUE`) is derived from the three taxa, never
  hand-flattened
- a new group extends `RuleGroupPrefix`, `RuleGroup`, and `RULE_GROUP_BY_PREFIX` together, or
  the congruence tests fail
- `--include=ACT` fails loudly as an unknown selector instead of silently meaning everything
