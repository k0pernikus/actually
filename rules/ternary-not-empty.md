<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTT002 — ternary-not-empty

**Group:** actually-ternaries
**Status:** unstable
**Auto-fix:** no

An arm that exists only for conditional inclusion — `None`, an empty string, an empty container
literal — is a hidden `else` smuggling an absent case into the binding: the result is a
`T | None` (or an empty sentinel) every consumer must branch on again. Resolve the absence
before the binding exists — raise on absent input, branch at the boundary, or accumulate with
guarded appends when optional parts multiply.

## Degenerate None arm

### Banned

```python
parsed = None if raw is None else parse(raw)
```

### Wanted

```python
def parsed(raw):
    if raw is None:
        raise ValueError("raw input is required")

    return parse(raw)
```

## Supersedes (stricter than ruff)

- `SIM108` — SIM108 (if-else-block-instead-of-if-exp) rewrites an `if`/`else` to a ternary — a form this rule allows, except when a branch is `None`/empty, which is the degenerate arm this rule forbids

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
