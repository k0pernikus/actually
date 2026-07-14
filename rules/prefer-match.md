<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTC005 — prefer-match

**Group:** actually-conditionals
**Status:** unstable
**Auto-fix:** no

A run of `if …: return` arms closed by a terminal `return` or `raise` enumerates a closed
decision, one arm per case — but written as sequential ifs the table is invisible and nothing
marks the enumeration complete. One `match` statement is the fixpoint, exactly as for `elif`
chains (ACTC002): a single dispatch point with an explicit default arm. The rule fires only
where the rewrite is safe and profitable — every condition inspects one shared scrutinee
(which `match` evaluates once), or every condition is free of calls and subscripts so hoisting
the conditions cannot change behaviour. Guard chains whose later conditions depend on earlier
arms having returned — a `parent is None` check narrowing what the next call may touch — are
exempt: those conditions must stay sequential. No auto-fix: choosing the scrutinee is
judgement, and a synthesized raising default arm would alter behaviour — a RISKY rewrite
reserved for a human.

## Banned

```python
def declaration(found, description):
    if found:
        return f"Found config. Running with: {description}"

    if description == ALL:
        return "No config found, running with default"

    return f"No config found, running with: {description}"
```

## Wanted

```python
def declaration(found, description):
    match found, description == ALL:
        case True, _:
            return f"Found config. Running with: {description}"

        case _, True:
            return "No config found, running with default"

        case _:
            return f"No config found, running with: {description}"
```

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
