<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTI003 — prefer-match

**Group:** actually-if-conditions
**Status:** unstable
**Auto-fix:** no

A run of `if …: return` arms that all compare the same subject, closed by a terminal `return`
or `raise`, enumerates a closed dispatch — but written as sequential ifs the table is
invisible, the subject is re-evaluated per arm, and nothing marks the enumeration complete.
One `match` statement on that subject is the fixpoint: a single dispatch point with an
explicit default arm, the scrutinee evaluated once. Or-patterns (`case 403 | 409:`) fold arms
sharing a body, class patterns (`case str():`) dispatch on type, and the default arm fails
loud — reaching for `dict.get(key, default)` instead trades the loud unknown-value failure
for a silent wrong answer. The rule fires only on a genuinely shared scrutinee — this is the
second pass after `no-elif` (ACTI002) has flattened a chain to guards. Chains of independent
predicates are guard clauses
and STAY guard clauses — fabricating a scrutinee to force a `match`
(`match found, description == ALL:` with positional `case True, _:` arms) is the same if-chain
wearing `match` syntax, and worse: the tuple positions carry unnamed roles. Dependent guard
chains — a `parent is None` check narrowing what the next call may touch — are equally exempt.
No auto-fix: a synthesized raising default arm would alter behaviour — a RISKY rewrite
reserved for a human.

## Banned

```python
def http_label(status):
    if status == 200:
        return "ok"

    if status == 404:
        return "missing"

    if status == 403:
        return "error"

    if status == 409:
        return "error"

    raise ValueError(status)
```

## Wanted

```python
def http_label(status):
    match status:
        case 200:
            return "ok"

        case 404:
            return "missing"

        case 403 | 409:
            return "error"

        case _:
            raise ValueError(status)
```

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
