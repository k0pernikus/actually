<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTE002 — no-for-else

**Group:** actually-completion-clauses
**Status:** stable
**Auto-fix:** no

The `else` clause on a `for` loop runs only when the loop finished without hitting a `break` —
overloading `else` to mean "completed", so the normal completion path sits in the branch that
reads as exceptional. Extract the search into a helper that returns early on a match; the
function tail then reads as the natural "nothing matched" case, with no `else` required.

## Banned

```python
def first_even(numbers):
    for number in numbers:
        if number % 2 == 0:
            return number
    else:
        return None
```

## Wanted

```python
def first_even(numbers):
    for number in numbers:
        if number % 2 == 0:
            return number

    return None
```

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
