<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTC002 — no-elif

**Group:** actually-conditionals
**Status:** stable
**Auto-fix:** no

An `elif` chain is N-way dispatch written as linear control flow: the reader evaluates every
arm in order to learn the routing. Structural pattern matching expresses the intent natively —
translated into a `match` statement the chain reaches its fixpoint: one dispatch point, an
explicit default arm (`case _`), and further reduction is a no-op. Class patterns
(`case str():`) cover type dispatch, and or-patterns (`case str() | list():`) fold arms that
share a body. A lookup table remains legitimate for a genuinely data-shaped value-to-value map
— but reaching for `dict.get(key, default)` to dodge the default arm trades the loud
unknown-value failure for a silent wrong answer. No auto-fix: synthesizing the default arm
means inventing a `raise` where the original silently fell through — a RISKY,
behaviour-altering rewrite reserved for a human.

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
    match code:
        case 200:
            return "ok"
        case 404:
            return "missing"
        case _:
            raise ValueError(f"unexpected code: {code}")
```

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
