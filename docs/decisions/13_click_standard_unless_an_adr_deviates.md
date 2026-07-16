# 13 — Click-Standard CLI Behavior Unless an ADR Deviates

**Status:** Accepted
**Created:** 2026-07-16
**Updated:** 2026-07-16
**See also:** [ADR 7](7_ci_report_formats_mirror_ruff.md), [ADR 8](8_help_reflects_the_active_selection.md)

## Context

- The CLI is built on rich-click / click, which already defines a convention for nearly every
  surface: option and flag naming, the `-h` / `--help` pair, `--version` output, exit codes, usage
  and error messages, parsing, and prompts.
- Re-implementing any of these by hand invites drift and surprise, costs maintenance, and throws
  away the least-surprise a click user already carries into the tool.
- Departures are sometimes warranted — selection-aware help
  ([ADR 8](8_help_reflects_the_active_selection.md)) and ruff-mirrored report formats
  ([ADR 7](7_ci_report_formats_mirror_ruff.md)) are deliberate ones — but they are the exception,
  and their reasoning belongs on the record, not buried in the code.

## Decision

- The CLI follows click's standard behavior by default. Where click defines an idiom, adopt it
  rather than invent one.
- Deviation is permitted, but every deviation MUST be recorded in its own ADR that names the
  click-standard it departs from and why. A deviation with no ADR is a defect.
- This ADR fixes only the default. It authorizes no specific deviation; each is its own decision.

## Consequences

- The CLI stays predictable for anyone who knows click; the burden of justification sits on the
  deviation, never on the default.
- Every departure is discoverable from the decision log rather than by reading the code — grep the
  ADRs to learn what diverges and why.
- A surface that quietly diverges from click without an ADR is a defect, closed by either
  conforming to click or recording the deviation's ADR.
