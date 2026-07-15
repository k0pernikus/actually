<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTI002 — no-elif

**Group:** actually-if-conditions
**Status:** stable
**Auto-fix:** no

An `elif` chain welds N decisions into one compound statement: every arm hangs off the first
`if`, the reader holds the whole ladder open, and inserting or reordering a case edits the
middle of the construct. The fixpoint is flat guard clauses — multiple `if` statements, each
with an early `return`, `raise`, `continue`, or `break` — nothing more: every decision stands
alone and appending a case is appending a statement. This rule bans exactly `elif`. When the
flattened arms all compare one shared subject, `prefer-match` (ACTI003) then escalates the
chain to a `match` statement — that judgement belongs to that rule, never to this one.

## Banned

```python
def access_level(user, resource):
    if user.is_admin:
        return "admin"
    elif resource.is_public:
        return "read"
```

## Wanted

```python
def access_level(user, resource):
    if user.is_admin:
        return "admin"

    if resource.is_public:
        return "read"

    return "none"
```

## Conflicts with ruff

- `PLR5501` — PLR5501 (collapsible-else-if) rewrites `else: if` into an `elif`, which this rule forbids

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
