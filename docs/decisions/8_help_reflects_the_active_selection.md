# 8 — Help Reflects the Active Selection

**Status:** Accepted
**Created:** 2026-07-14
**Updated:** 2026-07-14

## Context

- `check --help` / `format --help` used to be static prose naming every fix the tool ships
- rule selection (ADR 5, ADR 6) makes the actual changeset a function of `well-actually.toml`
  plus `--include` / `--exclude`: a static help oversells fixes the selection disables, and a
  reader cannot tell which of its claims apply to the invocation in front of them
- click renders help through an eager option that short-circuits parsing, so a naive dynamic
  help would see only the flags typed before `--help`

## Decision

- the help body for `check` and `format` is composed at render time from the resolved
  selection — the same `load_selection` path the run itself uses (cwd config file plus CLI
  flags), declared inside the help exactly as on stderr
- `format --help` partitions the enabled rules by fix capability: auto-fixed in full,
  auto-fixed where safe, reported only; a selection enabling no auto-fixable rule says exactly
  that instead of listing nothing
- `check --help` lists the enabled rules it will report
- composition is a pure function `(enabled, catalog, declaration) -> str` in
  `actually.help_text`; the CLI layer only resolves the selection and dispatches by command
  name
- `--include` / `--exclude` are eager and `--help` / `-h` is a custom non-eager option: click
  processes eager parameters first regardless of argv position, so the selection flags are
  always parsed before help renders — flag order never changes the rendered truth
- a broken selection (unknown selector, repeated selector, empty result) fails `--help` loudly
  with the same usage error as a run: help never renders against a selection the run would
  reject

## Consequences

- the help neither oversells nor undersells the changeset: every named rule is active, every
  active rule is named
- the static fix claims moved out of the command decorators; `rules.toml` summaries are the
  one source feeding CLI help, `rules --list`, the README tables, and the docs pages
- group help (`actually --help`) keeps static one-line command summaries; only the
  per-command body is dynamic
