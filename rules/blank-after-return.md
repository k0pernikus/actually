<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTR002 — blank-after-return

**Group:** actually-returns
**Status:** stable
**Auto-fix:** yes

Code on the line directly under a `return` — typically after the enclosing block dedents —
reads as if it belonged to the same thought. One blank line after the `return` marks that a
flow ended there and something new begins.

## Banned

```python
def f(foo, bar, baz):
    if foo:
        return foo
    if bar:
        return baz
```

## Wanted

```python
def f(foo, bar, baz):
    if foo:
        return foo

    if bar:
        return baz
```

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
