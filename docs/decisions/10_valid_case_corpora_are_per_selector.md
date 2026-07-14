# 10 — Valid-Case Corpora Are Per-Selector Test Sources

**Status:** Accepted
**Created:** 2026-07-14
**Updated:** 2026-07-14
**See also:** [ADR 5](5_rule_selection_by_prefix_specificity.md), [ADR 6](6_selector_taxonomy_rule_group_all.md)

## Context

- the single `python_sources/valid_cases/` corpus validated every example against every rule at
  once: an allowed shape for one rule could not be pinned without also satisfying all others, so
  per-rule allowlisting was impossible and cross-rule interplay was pinned only implicitly
- the corpus is a regression suite — code that must keep passing — so it belongs under `tests/`,
  next to the test module that pins it
- `format_source` composes its fixers in one fixed order — chains, literals, try/else dedent,
  return spacing — and that order is observable behaviour worth pinning on its own
- the selector taxonomy ([ADR 6](6_selector_taxonomy_rule_group_all.md)) already names exactly the
  granularities an allowlist needs: a rule code, a group prefix, and `__ALL__`

## Decision

- `tests/valid-code-checks/_src/` holds one directory per registered rule selector (`ACTH001/`,
  `ACTC/`, `__ALL__/`); every `*.py` inside is validated and format-pinned under **exactly that
  selection** by `tests/valid-code-checks/test_valid_python_code_passes_check.py`, resolved
  through the ADR 5 machinery (`resolve_selection((dir_name,), ())`) — an unknown directory name
  fails the tests loudly as an unknown selector
- a per-rule directory allowlists shapes atomically against its rule alone; its cases MAY violate
  other rules, so only the per-selector tests own the corpora — every tree-wide gate (`ruff` via
  `extend-exclude`, `actually check` and `ty check` via explicit path scoping in `mise.toml` and
  `hk.pkl`) leaves `tests/valid-code-checks/_src/` alone
- `__ALL__/` pins the composed behaviour of the whole rule set under the fixed fixer order named
  above; conflicts between rules surface and get decided here
- the corpora mutate only via `mise run format-valid-cases`: per-selector `format_source`
  (`scripts/format_valid_cases.py`), then full-settings `ruff format` — which MAY legitimately
  rewrite (magic-comma explosion, anchor layout) — then `ruff format --check` proving the
  composite converged; every committed case is thereby a joint actually-plus-ruff fixpoint. ty
  deliberately stays out: corpus cases are allowed-shape fragments whose names are undefined by
  construction
- every per-rule directory carries a `foreign_rule_shapes.py` planting shapes OTHER rules would
  flag and rewrite; they must survive verbatim under the directory's selector, so any selection
  leak — in the tests or the format script — fails loud instead of passing silently
- adding an allowed shape is dropping a file into the matching selector directory — the tests
  glob the directories, no wiring

## Consequences

- rules gain atomic, reviewable allowlists; an example documents exactly which rule sanctions it
- composed-order regressions (a fixer reordering changing bytes) fail the `__ALL__` pins
- a stray directory or typo'd selector name cannot silently pass — selector resolution rejects it
