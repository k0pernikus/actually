<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTE001 — no-try-else

**Group:** actually-completion-clauses
**Status:** stable
**Auto-fix:** partial

The `else` clause on `try`/`except` overloads `else` to mean "no exception was raised", putting
the normal, expected flow in the branch that reads as exceptional everywhere else in the
language. Dedent the continuation after the `except` clauses into straight-line code: it is
reached only when the `try` body raised nothing, which is exactly what following the block
already means. `format` rewrites this automatically when every `except` body exits (`return`,
`raise`, `continue`, `break`); when one falls through, the dedent would change behaviour, so it
is reported for human refactoring instead.

## Banned

```python
def describe(path):
    try:
        config = load(path)
    except ParseError:
        return "invalid"
    else:
        return describe(config)
```

## Wanted

```python
def describe(path):
    try:
        config = load(path)
    except ParseError:
        return "invalid"

    return describe(config)
```

## Conflicts with ruff

- `TRY300` — TRY300 (try-consider-else) recommends moving a `return` out of the `try` body into an `else:` clause — the completion clause this rule forbids

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
