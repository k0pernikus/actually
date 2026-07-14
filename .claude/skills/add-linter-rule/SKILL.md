---
name: add-linter-rule
description: Use whenever the user proposes a new actually lint or format rule ("add a rule for X", "lint for Y", "ban Z", "prefer A over B"). Gates the rule behind a ruff/ty redundancy check, drives a joint brainstorm of the detection before any code, and enforces the autofix-safety policy — a fix must never break code; behavior-altering fixers are RISKY and opt-in only.
---

# Add Linter Rule

Run the steps in order for every proposed rule. Do not write implementation code before step 2
is settled with the user — the brainstorm is joint, not a solo design pass.

## 1. Redundancy gate — actually covers only what ruff and ty cannot

Check, in order, and stop at the first hit:

1. actually's own catalog: active and retired entries in `src/actually/rules.toml`, plus the
   roadmap candidates in [ADR 1](../../../docs/decisions/1_ruff_style_rule_codes_in_named_groups.md).
2. ruff: search the rule catalog at <https://docs.astral.sh/ruff/rules/> and inspect the
   nearest candidates with `uv run ruff rule <CODE>` — read what the rule actually detects,
   not just its title. Nearby-but-narrower counts as NOT covered; name the residue precisely.
3. ty: type-shaped rules (narrowing, exhaustiveness, deprecation) belong to ty, never to
   actually.

Iff an existing rule expresses the ask: recommend enabling or configuring it (this repo's
`ruff.toml` / `ty.toml` are the recommended baselines) and stop — actually MUST NOT duplicate
it (README §Standing on Ruff and Ty). Iff a rule covers part of the ask: the new rule targets
only the uncovered residue, and the docs page names the ruff/ty rule it complements.

## 2. Brainstorm the check — with the user, before code

Present these deliverables and get the user's pick on every open fork:

- the defect class in one sentence (what goes wrong in code that carries the shape)
- a banned/wanted example pair — these become the `banned` / `wanted` fields in `rules.toml`
  and are validated by the linter itself at docs generation
- an ast-grep detection sketch: node kinds, structural conditions, and what is deliberately
  exempt (the exemptions are part of the rule, not an afterthought)
- a false-positive probe: run the sketch against this repo (`src`, `tests`, `scripts`) and
  list every hit, classified wanted-flag vs false positive. The repo self-hosts — every true
  hit must be fixed in the same change that lands the rule, so the hit list is also the
  migration cost estimate.
- group and next free code per ADR 1; status starts `unstable`

## 3. Autofix policy — a fix MUST NOT break code

- default is check-only: omit `fix` in `rules.toml`
- `full` / `partial` require a behavior-preservation argument stated during the brainstorm:
  the rewrite provably cannot change runtime semantics, with the guard named (the reference
  shape: try/else dedent applies only when every except body already exits) and idempotence
  pinned by a test (`format(format(x)) == format(x)`)
- a fixer that COULD alter behavior is RISKY. It MUST NOT ship as `full` / `partial`.
  Shipping it requires first extending the rule-metadata schema with an explicit risky
  marking and gating risky fixes behind an opt-in flag (ruff's `--unsafe-fixes` shape), off
  by default, with the warning carried on the docs page and in `rules --list`. Until that
  mechanism exists, the rule ships check-only.

## 4. Implementation checklist

- failing tests first: the banned example as a reproducing test before the collector exists
- registry: `RuleCode` / `RuleName` Literals and the `Rule` constant in
  `src/actually/violations.py`, appended to `RULES`
- collector in `src/actually/checks.py`; fixer in `src/actually/formatting.py` only per §3
- `rules.toml` entry: code, name, group, status, fix (iff any), summary, rationale, banned,
  wanted
- parametrized sibling tests per
  [ADR 3](../../../docs/decisions/3_sibling_test_cases_are_one_parametrized_test.md)
- fix every hit the rule finds in this repo — the self-check hook blocks any commit otherwise
- `mise run format`, `mise run test`, `mise run lint` all green; docs regenerate via the hk
  hook
