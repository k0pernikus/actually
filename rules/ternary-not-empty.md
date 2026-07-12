# ACTC004 — ternary-not-empty

**Group:** actually-conditionals
**Status:** unstable
**Auto-fix:** no

An arm that exists only for conditional inclusion — `None`, an empty string, an empty container
literal — is a hidden `else` smuggling an absent case into the binding: the result is a
`T | None` (or an empty sentinel) every consumer must branch on again. Resolve the absence
before the binding exists — raise on absent input, branch at the boundary, or accumulate with
guarded appends when optional parts multiply.

## Banned

```python
parsed = None if raw is None else parse(raw)
```

## Wanted

```python
def parsed(raw):
    if raw is None:
        raise ValueError("raw input is required")

    return parse(raw)
```

Generated from [`rules.toml`](../rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
