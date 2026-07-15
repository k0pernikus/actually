# 3 — Sibling Test Cases Are One Parametrized Test

**Status:** Accepted
**Created:** 2026-07-13
**Updated:** 2026-07-15

## Context

- the ternary-not-empty false-positive fix accumulated five near-identical tests, each one input against
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

The **property** is the invariant the test's name states: it MUST hold for every row without
disjunction, and a name that merely restates the call (`test_outline_matches`) names no
property. When more than one truthful family partition exists, the author picks one; no
partition may leave a sibling test standing as its own function, and every family holds at
least two rows — a single-row family is a standalone function in costume.

Two or more siblings MUST collapse into one `pytest.mark.parametrize` test:

- the test is named for the **property** (`test_valid_ternary_is_clean`), each row's mandatory
  `pytest.param(..., id=...)` names its **scenario** (`constant-separator`) in kebab-case
- every row owns its payload — rows never share constants or build on each other
  (Do-Repeat-Yourself for test inputs)
- a scenario graduates back to a standalone test ONLY when it needs what a row cannot carry —
  an extra assertion pinning a failure the shared assertion does not, or setup of its own;
  anything expressible as payload plus expected value stays a row
- a row whose expected value is its unchanged input is a fixpoint pin, legitimate ONLY in a
  family that also carries at least one transforming row; a family whose every row feeds
  input through unchanged pins nothing and MUST NOT exist

## Consequences

- the failure report names the scenario precisely
  (`test_valid_ternary_is_clean[constant-separator]`)
- adding a scenario is one `pytest.param` row, not a new function
- the suite's function count tracks properties, not scenarios
