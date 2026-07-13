# 7 — CI Report Formats Mirror Ruff

**Status:** Accepted
**Created:** 2026-07-13
**Updated:** 2026-07-13

## Context

- CI platforms ingest linter findings through platform-specific report formats: GitLab's
  `codequality` artifact takes a Code Climate JSON subset, GitHub renders inline annotations
  from workflow commands and ingests SARIF for code scanning
- ruff's `--output-format` / `--output-file` pair is the vocabulary Python CI configs already
  speak (the gitlab-cicd-components python-linter template consumes exactly
  `ruff check --output-format=gitlab --output-file=gl-code-quality-report.json`)

## Decision

- one `--output-format` enum on `check` and `format` — never per-platform boolean flags:
  `text` (default, the terminal line format), `gitlab` (Code Climate JSON), `github`
  (workflow-command annotations), `sarif` (SARIF 2.1.0, the generic standard, also GitHub
  code scanning's upload format)
- `--output-file PATH` writes the report; the default `-` means stdout
- the vocabulary is the closed `OutputFormat` `Literal`; the boundary string narrows through
  one derived lookup, exactly like rule selectors (ADR 6)
- renderers are pure functions over `Finding` values (path + violation); `fixed:` notices and
  the selection declaration go to stderr so a report on stdout stays machine-clean
- gitlab: `check_name` = rule code, `severity` = `major` (ruff parity), `fingerprint` =
  sha256 of `path:code:line:message` — stable across runs, distinct per finding
- sarif: `level` = `warning`, driver rules carry `helpUri` pointing at the per-rule docs page
- reports carry paths exactly as passed — path shape is the invoker's contract; a CI job MUST
  invoke from the repo root with relative paths (GitLab resolves Code Climate paths against
  the repo root)

## Consequences

- the GitLab job is one line plus an artifact declaration; no jq/jello post-processing
- exit codes are unchanged by the format: findings still fail `check`, and
  `format --only-autofixable` still exits 0
- a future platform format is a new `Literal` member and renderer, not a new flag
