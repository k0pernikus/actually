# 5 — Rule Selection by Prefix Specificity

**Status:** Accepted
**Created:** 2026-07-13
**Updated:** 2026-07-15
**See also:** [ADR 1](1_ruff_style_rule_codes_in_named_groups.md)

## Context

- users need to run arbitrary subsets of the rule set — one rule only, everything except a
  group, a group minus one rule — without the tool dictating a fixed menu
- ruff's `select`/`ignore` prefix-specificity model is the convention Python linter users
  already read fluently; ADR 1's code scheme (group prefix + number) makes prefixes coincide
  with groups for free

## Decision

- selection lives in `well-actually.toml` (keys `include`, `exclude`, arrays of strings) and
  on the CLI (`--include` / `--exclude`, repeatable); a CLI list, when given, replaces the
  config file's corresponding list wholesale
- the config file is sourced from the current working directory ONLY — no walking up the
  tree, no merging; the invocation declares what it found and the resolved selection on
  stderr (`Found well-actually.toml. Running with: …` / `No well-actually.toml found,
  running with default '__ALL__'`), so the active subset is never ambient
- entries are rule codes (`ACTI001`), group prefixes (`ACTI`), or the `__ALL__` all-group —
  the three-taxon vocabulary of [ADR 6](6_selector_taxonomy_rule_group_all.md); never rule
  names or group display names
- untrusted strings from CLI and TOML narrow through one boundary lookup
  (`RULE_SELECTOR_BY_VALUE`, derived from the taxa — never hand-enumerated) and an unknown
  value fails there
- resolution is specificity, not order: for each rule the longest matching entry wins;
  `__ALL__` matches everything at length zero. A tie cannot arise: for any rule, equal-length
  matching entries are the same selector, and a repeated selector is already a hard error
- `include` defaults to `__ALL__`; `exclude` defaults to empty — the wanted state is running
  everything, and exclude-only workflows need no include
- hard errors, never silent tolerance:
    - any selector appearing more than once across `include` and `exclude` — a repeat inside
      one list restates, the same selector in both lists contradicts; both are authoring
      mistakes
    - `exclude = __ALL__` without at least one explicit include entry — a linter selected to
      check nothing
    - an entry outside the selector taxonomy of
      [ADR 6](6_selector_taxonomy_rule_group_all.md) — a registered rule code, a registered
      group prefix, or `__ALL__`; a substring like `ACT` or `ACTI00` is a prefix of registered
      codes yet still fails — a typo must never silently become a no-op
    - a resolved selection that enables zero rules
- `format` obeys the same selection: a disabled rule contributes neither reports nor fixes

## Consequences

- every subset is expressible: `exclude = ["__ALL__"]` + `include = ["ACTI001"]` runs one
  rule; `exclude = ["ACTL"]` drops a group; `exclude = ["ACTL"]` +
  `include = ["__ALL__", "ACTL001"]` drops a group but keeps one member
- selection failures surface as usage errors naming the valid vocabulary
- a future rule joins the vocabulary through the registry alone; the selection code never
  changes
