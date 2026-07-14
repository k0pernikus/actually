<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTH001 — multi-line-chain

**Group:** actually-chains
**Status:** unstable
**Auto-fix:** partial

A fluent chain reads one step per line — but ruff format joins any chain that fits the line
length, parentheses or not; its preview fluent style engages only past the limit, and no chain
analog of the magic trailing comma exists (astral-sh/ruff#8598). The one layout signal a
formatter cannot cross is a comment, and only on the chain's base-receiver line — on the open
paren it pins the parentheses while the chain inside still joins. `format` therefore rewrites
every chain of two or more invocations to break at the first call, one call per line, and
anchors the base line with `# well-actually: multi-line`; run before `ruff format`, the anchored
layout is a fixpoint of both tools. Consecutive attribute-only steps share one line
(`.parent.parent`), and a short chain — fewer than three invocations and fewer than three dot
steps — additionally parenthesizes its base receiver (`(make(1))`): without those parens ruff
re-renders the short head flat and relocates the anchor to the joined line's end. A stale
anchor — its chain shrunk below two
invocations — is stripped so the directive cannot rot. Chains carrying foreign comments or
multiline arguments are reported for human layout instead, and chains inside f-string
interpolations are exempt.

## Banned

```python
command = CommandLine.of("git").subcommand("config").argument(key)
```

## Wanted

```python
command = (
    CommandLine  # well-actually: multi-line
    .of("git")
    .subcommand("config")
    .argument(key)
)
```

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
