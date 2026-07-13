# 5 — Rule Selection by Prefix Specificity

**Status:** Accepted
**Created:** 2026-07-13
**Updated:** 2026-07-13
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
- the config file is discovered by walking up from the working directory; the nearest file
  wins; no file means defaults
- entries are rule codes (`ACTC004`), group prefixes (`ACTC`), or the `__ALL__` all-group —
  the three-taxon vocabulary of [ADR 6](6_selector_taxonomy_rule_group_all.md); never rule
  names or group display names
- untrusted strings from CLI and TOML narrow through one boundary lookup
  (`RULE_SELECTOR_BY_VALUE`, derived from the taxa — never hand-enumerated) and an unknown
  value fails there
- resolution is specificity, not order: for each rule the longest matching entry wins;
  `__ALL__` matches everything at length zero; a tie goes to `exclude`
- `include` defaults to `__ALL__`; `exclude` defaults to empty — the wanted state is running
  everything, and exclude-only workflows need no include
- hard errors, never silent tolerance:
    - `__ALL__` more than once across both lists — the second occurrence contradicts the
      first or restates it; both are authoring mistakes
    - `exclude = __ALL__` without at least one explicit include entry — a linter selected to
      check nothing
    - an entry that is neither `__ALL__` nor a prefix of a registered code — a typo must
      never silently become a no-op
    - a resolved selection that enables zero rules
- `format` obeys the same selection: a disabled rule contributes neither reports nor fixes

## Consequences

- every subset is expressible: `exclude = ["__ALL__"]` + `include = ["ACTC004"]` runs one
  rule; `exclude = ["ACTL"]` drops a group; `exclude = ["ACTL"]` +
  `include = ["__ALL__", "ACTL001"]` drops a group but keeps one member
- selection failures surface as usage errors naming the valid vocabulary
- a future rule joins the vocabulary through the registry alone; the selection code never
  changes
