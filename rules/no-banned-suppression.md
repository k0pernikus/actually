<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTS001 — no-banned-suppression

**Group:** actually-suppressions
**Status:** unstable
**Auto-fix:** no

A lint rule a project enables states a decision; a `# noqa` on that rule silences the decision at
one line while leaving the rule enabled everywhere else, so the codebase reports compliance it does
not have. A suppression records where a rule is still unmet — it never grants an exception to it.
This rule fires only on the codes listed under `banned-noqa` in `well-actually.toml`, so a project
names the rules whose suppression it refuses; every other `# noqa` is untouched, because plenty of
them are legitimate. A bare `# noqa` names no code and therefore silences the banned ones too, so
it fires whenever `banned-noqa` is non-empty. Ruff cannot express this: `RUF100` reports an UNUSED
directive, never a used one suppressing a rule you forbid suppressing.

## Suppressing a banned rule

With `banned-noqa = ["TID251"]`, the suppression is the finding. The directive does not make the
banned call acceptable; it records that the rule is unmet at that line.

### Banned

```python
value = os.environ["HOME"]  # noqa: TID251
```

### Wanted

```python
value = load(HomeSettings).home
```

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
