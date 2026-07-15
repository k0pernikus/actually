# 11 — Rule Identifiers Are Unstable Pre-1.0

**Status:** Accepted
**Created:** 2026-07-15
**Updated:** 2026-07-15
**See also:** [ADR 1](1_ruff_style_rule_codes_in_named_groups.md), [ADR 2](2_rule_docs_generated_from_rules_toml.md)

## Context

- [ADR 1](1_ruff_style_rule_codes_in_named_groups.md) promised a *stable* `{prefix}{NNN}` code
  per rule — never renumbered, never recycled — modelled on ruff, whose codes are a public
  contract users pin against
- that promise was premature: the grouping itself is still being discovered. The original
  `actually-conditionals` group has already been split into `actually-if-conditions`,
  `actually-ternaries`, and `actually-completion-clauses`, and the monolithic `no-else` rule
  into `no-if-else`, `no-try-else`, `no-for-else`, and `no-while-else` — a reshape that renamed
  and renumbered every conditional rule. Freezing codes before the taxonomy settles would
  ossify a grouping we already know was wrong
- `actually` is pre-1.0 and installed with a version pin (`well-actually@latest` re-resolves;
  `uv tool install` pins). A consumer's stable handle is the *version*, not the code

## Decision

- rule codes, names, and groups are **not stable** while `actually` is pre-1.0; they may take
  breaking changes at will — renamed, renumbered, split, merged, or regrouped — in any release
- the mechanism ADR 1 established stands unchanged: codes remain `{prefix}{NNN}` within a
  named `actually-{group}`, the registry in `violations.py` and `rules.toml` stay congruent,
  and CLI output still reports `{file}:{line} {code} [{name}] {message}`. Only the *stability
  guarantee* over those identifiers is retracted
- consumers pin a version and re-read the catalog (`actually rules --list`, the generated
  `README.md` and `rules/*.md`) after upgrading; they MUST NOT depend on a specific code or
  name surviving across releases
- the never-recycle discipline is suspended with the stability guarantee: a freed code or name
  MAY be reused for an unrelated rule pre-1.0, so a pinned old version and a new one can label
  different rules with the same code — another reason the version is the only stable handle
- at 1.0 this ADR is revisited: the taxonomy is declared settled and ADR 1's stable-code
  guarantee is reinstated from that point forward

## Consequences

- the reshape into `actually-if-conditions` / `actually-ternaries` / `actually-completion-clauses`
  ships as an ordinary change, needing no supersession ceremony per freed code
- ADR 1's Allocation table is explicitly a point-in-time snapshot, not a live contract; the live
  ledger is the `violations.py` + `rules.toml` registry, and the generated docs are its rendering
- a downstream `well-actually.toml` or CI selection can break on upgrade when a code or group
  prefix it names is renamed; this is expected pre-1.0 and the README states it at the top
- reinstating stability at 1.0 is a one-way ratchet — once declared, the never-renumber and
  never-recycle rules of ADR 1 bind again, so the pre-1.0 window is the only time to get the
  taxonomy right
