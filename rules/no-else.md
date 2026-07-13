<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTC001 — no-else

**Group:** actually-conditionals
**Status:** stable
**Auto-fix:** partial

An `else` clause hides the happy path one indent deeper and forces the reader to hold both
branches open. The completion clauses on `for`, `while`, and `try` are worse: they overload
`else` to mean "ran without `break`" or "raised no exception", putting the normal flow in the
branch that reads as exceptional everywhere else in the language. Invert the condition into a
guard clause and return early; dedent the continuation after `except`. `format` rewrites the
`try`/`except`/`else` case automatically when every `except` body already exits — the other
forms are reported for human refactoring.

## Banned

```python
def describe(config):
    if config is None:
        return "missing"
    else:
        return str(config)
```

## Wanted

```python
def describe(config):
    if config is None:
        return "missing"

    return str(config)
```

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
