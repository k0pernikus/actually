# 2 — Rule Docs Generated From rules.toml

**Status:** Accepted
**Created:** 2026-07-13
**Updated:** 2026-07-13
**See also:** [ADR 1](1_ruff_style_rule_codes_in_named_groups.md)

## Context

- rule metadata (lifecycle, fixability, prose) lived only in hand-written README text, free to
  drift from the code registry in `violations.py`
- sentinel's `README.template.md` + generator + hk regenerate-and-stage hook keeps generated
  docs in lockstep with their sources; the same shape fits here
- documentation examples rot silently unless something executes them

## Decision

- `rules.toml` is the single source of rule metadata: per rule a `[[rules]]` table with
  `code`, `name`, `group`, `status`, `summary`, `rationale`, a `banned` and a `wanted` example,
  and optionally `fix`
- `status` is exactly one of `unstable`, `stable`, `removed`; a removed rule keeps its row
  (codes are never recycled, per ADR 1) carrying only `code`, `name`, `group`, `status`
- every rule is checkable by definition; `fix` declares what `format` can rewrite — `full`,
  `partial`, or absent (check-only). A boolean cannot express `no-else`, whose `try/else`
  dedent fixes only a sub-case, so the key is three-valued by omission
- `scripts/generate_docs.py` renders `README.md` (from `README.template.md`, rules table with
  per-rule links) and one `rules/{name}.md` page per active rule (rationale + banned/wanted
  examples); it deletes stray pages and refuses to run when `rules.toml` disagrees with the
  code registry
- the generator validates every example with the linter itself: a `banned` snippet must
  trigger its own rule, a `wanted` snippet must be violation-free — doc rot fails the build
- an hk pre-commit job regenerates and stages the outputs when any source changes; a pre-push
  check and an integration test (`--check`) gate freshness in CI
- the generator leaves every output chmod `444` and toggles write access only while writing —
  a hand edit hits a read-only file first; the mode is per-checkout state (git does not track
  it), re-applied whenever the generator runs, and `--check` deliberately ignores it so a fresh
  clone passes CI

## Consequences

- editing `README.md` or `rules/*.md` by hand is futile — the hook overwrites them; edit
  `rules.toml` or `README.template.md`
- a new rule ships with its documentation or not at all: the congruence check fails on a
  registry/TOML mismatch, the snippet check fails on missing or wrong examples
- `unstable` marks a rule whose semantics may still change in a MINOR release; `stable` rules
  change semantics only with a deprecation path
