<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTL002 — one-element-per-line

**Group:** actually-literals
**Status:** unstable
**Auto-fix:** partial

Json-like structures read as records: one element per line with the brackets on their own
lines makes membership scannable and keeps every future diff to the single line it concerns.
The fix rewrites the literal in place; a literal carrying comments or multiline elements is
reported for human formatting instead. Tuples are exempt — they appear in subscripts and type
expressions where this layout is not wanted.

## Banned

```python
point = {"x": 1, "y": 2}
```

## Wanted

```python
point = {
    "x": 1,
    "y": 2,
}
```

Generated from [`rules.toml`](../rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
