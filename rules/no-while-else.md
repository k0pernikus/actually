<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTE003 — no-while-else

**Group:** actually-completion-clauses
**Status:** stable
**Auto-fix:** no

The `else` clause on a `while` loop runs only when the condition became false without a
`break` — the same overload as `for`/`else`, hiding the normal completion path in the
exceptional-looking branch. Restructure so the after-loop code follows the loop directly: a
`break`-search becomes a guard that returns on the match, with the fall-through as the
completion case.

## Banned

```python
def scan(source, target):
    while source.has_next():
        if source.peek() == target:
            return source.take()
    else:
        return None
```

## Wanted

```python
def scan(source, target):
    while source.has_next():
        if source.peek() == target:
            return source.take()

    return None
```

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
