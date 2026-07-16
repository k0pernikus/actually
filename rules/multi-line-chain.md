<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTH001 — multi-line-chain

**Group:** actually-chains
**Status:** unstable
**Auto-fix:** partial

A fluent chain reads one step per line — but ruff format joins any chain that fits the line
length, parentheses or not; its preview fluent style engages only past the limit, and no chain
analog of the magic trailing comma exists (astral-sh/ruff#8598). The one layout signal a
formatter cannot cross is a comment, and only on the chain's base-receiver line — on the open
paren it pins the parentheses while the chain inside still joins. A chain is two or more method
calls, or a method call together with a property access, counting only the steps after the base
receiver (`x.a().b()`, `x.a().b`, `Path(n).resolve().parent`); a lone trailing call on a receiver
(`make(1).build()`, `worktree_index_path(w).exists()`, `self.page.locator(x)`) is not a chain and
stays on one line. `format` rewrites every chain to break at the first call, one call per line,
and anchors the base line with `# well-actually: multi-line` — the base is the receiver of that
first call, so leading receiver attributes (`self.page`) fold onto it and never count toward the
threshold; run before `ruff format`, the anchored layout is a fixpoint of both tools. Consecutive
attribute-only steps share one line (`.parent.parent`), an attribute between two calls rides with
the call after it (`.b.bar()`), and a chain ruff would render flat when bare — one with fewer than
two attribute accesses whose value is a call or subscript, such as a call-terminated two-call
chain — additionally parenthesizes its base receiver (`(resolved)`, `(b)`): without those parens
ruff re-renders the short head flat and relocates the anchor to the joined line's end. A multiline
argument on a chain step is kept intact and re-indented under the anchored layout; only chains
carrying a foreign comment are reported for human layout, and chains inside f-string
interpolations are exempt. A stale anchor — its chain shrunk below the threshold — is stripped so
the directive cannot rot. This wanted state is a deliberate middle-ground: an attribute between two
calls rides with its call and a short chain keeps its base parens, because otherwise ruff re-joins
them. `ruff format` exposes no toggle to relax this; a native fluent-chain control
(astral-sh/ruff#8598) would retire the compromise.

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
