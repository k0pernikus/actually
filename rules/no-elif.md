<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTC002 — no-elif

**Group:** actually-conditionals
**Status:** stable
**Auto-fix:** no

An `elif` chain is N-way dispatch written as control flow: the reader walks every arm in order
to learn which one matters. Dispatch is data, not code — a lookup table, a `match` statement,
or a strategy map. A new case becomes a new entry, never a new `elif`.

## Banned

```python
def label(code):
    if code == 200:
        return "ok"
    elif code == 404:
        return "missing"
```

## Wanted

```python
def label(code):
    labels = {
        200: "ok",
        404: "missing",
    }

    return labels.get(code, "unknown")
```

Generated from [`rules.toml`](../rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
