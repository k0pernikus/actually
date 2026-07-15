# 12 — Autofixables Are Mechanical Sanitation, Not Human Findings

**Status:** Accepted
**Created:** 2026-07-15
**Updated:** 2026-07-15
**See also:** [ADR 2](2_rule_docs_generated_from_rules_toml.md), [ADR 9](9_anchor_comments_pin_layout_ruff_cannot_express.md)

## Context

- `actually`'s violations split by whether `format` can resolve them. Some it rewrites
  mechanically; others it must leave — either the rule has no fixer, or a partial-fix rule cannot
  safely rewrite that particular instance. Which rules and which instances fall on each side is not
  fixed: a better ast-grep approach can move a case from the un-fixable group into the mechanical
  one, so the split is a property of each violation, never a hard-coded list
- the two kinds want opposite handling. A mechanical fix is noise to a human — the tool just
  applies it — yet friction if it blocks a formatting pipeline. A refactor-demanding finding is the
  reverse: it needs a human's attention and time, and it drowns if every mechanical nit is streamed
  beside it
- before this decision `format` reported the whole un-fixable remainder on every run (even under
  `--only-autofixable`), spamming the formatter path, while `check` reported everything with no way
  to separate the mechanical from the manual — so neither command served either audience

## Decision

- adopt the principle: an **autofixable** violation is mechanical code-sanitation — applied
  automatically in a commit hook or CI pipeline, never surfaced to a human; a **non-autofixable**
  violation is a code-quality report — surfaced first and driven to zero over time, at human pace
- `autofixable` is a property of each violation: true when the fixer resolves that violation,
  decided on the original source so its line stays real (never a before/after-`format` diff, which
  shifts lines). A rule whose fixer is total marks all its violations autofixable, a rule with no
  fixer marks none, and a partial fixer decides per instance via the same planner it runs. The
  fixer's reach — which rules, which instances — is declared with the rules
  ([ADR 2](2_rule_docs_generated_from_rules_toml.md)'s `rules.toml`) and can only widen; this ADR
  fixes the principle, not the current reach
- `format` applies every autofixable, prints only the files it changed, stays silent on a no-op,
  and exits 0; it never reports the non-autofixable remainder — that is not its job
- `check` reports all violations by default; `check --only-autofixable` reports only the mechanical
  set (the "is it sanitized?" gate for the formatter path) and `check --ignore-autofixable` reports
  only the manual set (the standing code-quality report). The two filters are mutually exclusive

## Consequences

- `format` becomes a quiet formatter in the `ruff format` mold — apply and exit, no findings
  stream. `--only-autofixable` leaves `format` (its behaviour is now the sole default) and reappears
  on `check` as a filter, paired with the new `--ignore-autofixable`
- the mechanical path and the human path decouple: a commit hook or CI runs `format` (and
  `check --only-autofixable` to assert it ran) with no human in the loop, while
  `check --ignore-autofixable` is the report a human triages and clears over time
- a partial-fix rule's un-rewritten instances are non-autofixable and land in the code-quality
  report, never in `format`'s output — [ADR 9](9_anchor_comments_pin_layout_ruff_cannot_express.md)'s
  reported-only chains are today's instance of this; a later approach that makes such a case fixable
  simply moves it into `format`'s mechanical set
- a rule's declared fixer reach and its violations' `autofixable` flags are two expressions of one
  fact, kept consistent — a rule the fixer never touches marks nothing autofixable, one it always
  resolves marks everything
- the split generalizes past today's safe mechanical fixes: a future best-effort tier — riskier
  rewrites that push toward the wanted state but may need review — fits as an opt-in beyond what
  `format` applies by default, widening the fixer's reach without disturbing the format/check
  relationship; "no human in the loop" holds for the safe mechanical set, and anything less certain
  is opt-in
