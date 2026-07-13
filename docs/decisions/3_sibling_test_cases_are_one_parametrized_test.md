# 3 — Sibling Test Cases Are One Parametrized Test

**Status:** Accepted
**Created:** 2026-07-13
**Updated:** 2026-07-13

## Context

- the ACTC004 false-positive fix accumulated five near-identical tests, each one input against
  the same clean-verdict assertion — the suite grows a function per scenario while the pinned
  property stays singular
- pytest's `parametrize` (PHPUnit vocabulary: data provider) expresses exactly this: one named
  property, N labelled scenarios

## Decision

**Sibling test cases** are tests that satisfy all three:

1. they exercise the **same public unit** through the same call shape;
1. they pin the **same property with the same assertion structure** — the expected value may
   vary per row, the assertion's shape may not;
1. they differ **only in the input payload** (and its paired expected value) — no scenario
   needs its own setup, fixtures, or extra assertions.

Three or more siblings MUST collapse into one `pytest.mark.parametrize` test:

- the test is named for the **property** (`test_valid_ternary_is_clean`), each row's mandatory
  `pytest.param(..., id=...)` names its **scenario** (`constant-separator`) in kebab-case
- every row owns its payload — rows never share constants or build on each other
  (Do-Repeat-Yourself for test inputs)
- a scenario that outgrows the shared shape — an extra assertion, its own setup — graduates
  back to a standalone test; the family keeps the rest
- two siblings stay standalone tests: pair-churn buys no scanability

Out of scope stays out: tests whose arrange differs structurally (per-scenario filesystem
layouts), composite real-world pins whose provenance is the point, and rows that would feed
input through unchanged into an identity assertion (banned as tautology regardless of shape;
a no-op verdict from a real decision — `format_source` leaving unsafe code alone — is a
legitimate row, not an identity row).

## Consequences

- the failure report names the scenario precisely
  (`test_valid_ternary_is_clean[constant-separator]`)
- adding a scenario is one `pytest.param` row, not a new function
- the suite's function count tracks properties, not scenarios
