<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTT001 — ternary-not-nested

**Group:** actually-ternaries
**Status:** stable
**Auto-fix:** no

A ternary is the one permitted conditional expression, and only flat: a ternary nested inside
either arm is an `elif` chain in expression form, with reading order collapsing at exactly the
point where clarity matters most. Refactor to guard clauses — or, when the arms dispatch on a
single subject, one `match` statement (ACTI003).

## Banned

```python
action = "beach" if sunny else "sleep" if night else "home"
```

## Wanted

```python
def action(sunny, night):
    if sunny:
        return "beach"

    if night:
        return "sleep"

    return "home"
```

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
