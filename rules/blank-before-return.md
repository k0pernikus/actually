# ACTR001 — blank-before-return

**Group:** actually-returns
**Status:** stable
**Auto-fix:** yes

A `return` that follows other statements in its block is the exit point of the function —
stacked flush against the work above it, it reads as just another line. One blank line above
marks the handoff from computing the value to leaving with it.

## Banned

```python
def f(baz):
    if baz:
        foo = 42 + 1337
        return foo
```

## Wanted

```python
def f(baz):
    if baz:
        foo = 42 + 1337

        return foo
```

Generated from [`rules.toml`](../rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
