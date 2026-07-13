# 1 — Ruff-Style Rule Codes in Named Groups

**Status:** Accepted
**Created:** 2026-07-13
**Updated:** 2026-07-13

## Context

- rules were addressed by bare kebab slugs (`no-else`) with no grouping and no identifier that
  survives a message or slug rewording
- ruff's `{PREFIX}{NNN}` scheme is the convention users of a Python linter already read fluently
- future features (per-rule select/ignore, per-rule docs) need a stable short id

## Decision

- every rule belongs to exactly one group named `actually-{group}`, grouped by the language
  construct it governs — never by rule flavor
- every group owns the code prefix `ACT` plus one unique uppercase letter; a letter is allocated
  here, once, and never reused for another group
- every rule has a stable code `{prefix}{NNN}` (three digits, sequential within its group) and a
  kebab-case name; codes are never renumbered and never recycled — a retired rule leaves a hole
- the registry in `violations.py` mirrors the allocation table below; a new rule lands as a row
  here first, then as code
- CLI output reports `{file}:{line} {code} [{name}] {message}` on every violation

### Allocation

| Code | Name | Group |
|:---|:---|:---|
| ACTC001 | no-else | actually-conditionals |
| ACTC002 | no-elif | actually-conditionals |
| ACTC003 | ternary-not-nested | actually-conditionals |
| ACTC004 | ternary-not-empty | actually-conditionals |
| ACTL001 | trailing-comma | actually-literals |
| ACTL002 | one-element-per-line | actually-literals |
| ACTR001 | blank-before-return | actually-returns |
| ACTR002 | blank-after-return | actually-returns |

Reserved group letters: `C` (conditionals), `L` (literals), `R` (returns).

### Rule semantics

- ACTC001 bans every `else` clause — on `if`, and the completion clauses on `for`, `while`,
  and `try` alike
- ACTC002 bans `elif`; N-way dispatch is data (lookup table, `match`, strategy map), not code
- ACTC003 bans a ternary inside another ternary's arm — `elif` in expression form
- ACTC004 bans a degenerate ternary arm (`None`, `""`, an empty container literal): conditional
  inclusion in disguise, and a `None` arm additionally smuggles a `T | None` into the binding
  (`parsed = None if raw is None else parse(raw)`)
- ACTR001/ACTR002 require a blank line above a `return` that follows other statements in its
  block, and below a `return` when more code follows

## Roadmap

Candidate rules consistent with the enforced style, named here without allocated codes — a code
is allocated only when the rule is implemented:

- no-nested-if — an `if` directly inside another `if`; invert the outer check into a guard
- no-boolean-collapse — collapsing distinct checks into `and`, and OR-chains
  (`if a or b or c:`) that fake-flatten what should be guards or a dispatch table
- convergent branch extraction — both arms setting the same variable before a common tail is
  not an `else` exception; the diverging part belongs in a helper guarded at the call site
- suite-on-its-own-line — one-liner suites (`if x: return`) as a layout group candidate,
  which would claim a new group letter

## Consequences

- the code, not the message, is the parseable contract; messages may reword freely
- adding a rule with a colliding code or name fails `tests/test_rules.py`
- consumers of the Python API receive `Violation.rule` as a `Rule` value object
  (code, name, group) rather than a bare string
