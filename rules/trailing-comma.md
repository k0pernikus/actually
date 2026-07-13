<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTL001 — trailing-comma

**Group:** actually-literals
**Status:** unstable
**Auto-fix:** yes

Appending, removing, or reordering an element should touch exactly one line — without the
trailing comma the previous last element changes too, polluting every diff. The comma is also
the magic trailing comma that formatters (ruff, black) respect, pinning the multiline layout
instead of collapsing it back to one line.

## Banned

```python
labels = {
    200: "ok",
    404: "missing"
}
```

## Wanted

```python
labels = {
    200: "ok",
    404: "missing",
}
```

Generated from [`rules.toml`](../rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
