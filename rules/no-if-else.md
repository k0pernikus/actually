<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTI001 — no-if-else

**Group:** actually-if-conditions
**Status:** stable
**Auto-fix:** no

An `else` on an `if` hides the happy path one indent deeper and forces the reader to hold both
branches open at once. Invert the condition into a guard clause and exit early — `return`,
`raise`, `continue`, `break` — so the primary flow stays at the top indent and each decision
reads on its own. The `else` keyword inside a conditional expression is NOT this rule's target:
a flat ternary (`x = "a" if cond else "b"`) stays valid — its limits are ternary-not-nested
(ACTT001) and ternary-not-empty (ACTT002). The completion `else` on `for`, `while`, and `try`
is a different overload, banned separately by no-for-else (ACTE002), no-while-else (ACTE003),
and no-try-else (ACTE001).

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

## Supersedes (stricter than ruff)

- `PLR5501` — PLR5501 (collapsible-else-if) de-nests `else:` wrapping an `if` to `elif … else`; this rule goes further, banning any `else` on an `if`, so PLR5501's output still needs flattening to guard clauses

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
