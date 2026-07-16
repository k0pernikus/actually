# 9 — Anchor Comments Pin Layout Ruff Cannot Express

**Status:** Accepted
**Created:** 2026-07-14
**Updated:** 2026-07-16
**See also:** [ADR 1](1_ruff_style_rule_codes_in_named_groups.md), [ADR 2](2_rule_docs_generated_from_rules_toml.md)

## Context

- ruff format joins any call chain that fits `line-length`, parentheses or not; its preview
  fluent style ([astral-sh/ruff#8598](https://github.com/astral-sh/ruff/issues/8598), shipped in
  0.14.10 via [PR #21369](https://github.com/astral-sh/ruff/pull/21369)) engages only past the
  limit, and no chain analog of the magic trailing comma exists
  ([discussion #14277](https://github.com/astral-sh/ruff/discussions/14277))
- a comment is the one token a Black-lineage formatter cannot join across, and placement decides
  its reach — probed live under the recommended config (preview, line-length 180): on the chain's
  base-receiver line it pins the entire fluent layout; on the open paren or on its own line it
  pins only the parentheses while the chain inside still joins
- the base-line anchor alone holds only a chain ruff keeps fluent — one with at least two
  attribute accesses whose value is a call or subscript (a call-terminated chain of three or more
  calls, or an attribute-terminated chain of two or more); a receiver's own attribute path
  (`self.page`) and an attribute sitting between two calls never add to that count. A chain below
  it — a call-terminated two-call chain such as `make(1).build()` — is re-rendered flat with the
  anchor relocated to the joined line's end, unless the base receiver carries its own parentheses,
  which ruff never dissolves around a comment-bearing expression; `(make(1))  # well-actually:
  multi-line` pins where bare `make(1)` does not. Consecutive attribute-only steps ride one line
  (`.parent.parent`), and an attribute between two calls rides with the call after it
  (`.b.bar()`) — as far as ruff breaks; nesting parens to isolate a middle step further, ruff
  tolerates but is deliberately not emitted
- ACTL001 already exploits the same mechanism class: `actually` plants the one token ruff
  respects (there the magic trailing comma), and the actually-then-ruff composition converges

## Decision

- directive comments are namespaced by the package's full name — `# well-actually: <directive>`
  — matching the ecosystem convention (`# noqa`, `# shellcheck …`, `# ty: ignore`); the first
  directive is `multi-line`
- ACTH001 (multi-line-chain) requires every chain laid out one call per line, broken at the first
  call, with `# well-actually: multi-line` anchoring the base-receiver line. A chain is two or more
  method calls, or a method call together with a property access, counting only the steps after the
  base receiver: `x.a().b()`, `x.a().b`, and `Path(n).resolve().parent` are chains; a lone trailing
  call on a receiver (`make(1).build()`, `worktree_index_path(w).exists()`, `self.page.locator(x)`)
  is a single step and stays on one line. The base is the receiver of that first step, so leading
  receiver attributes (`self.page`) fold onto it and never count toward the threshold; attribute-only
  runs and an attribute between calls share a line with the call after them, and a chain ruff would
  render flat when bare — one with fewer than two call-valued attribute accesses, such as a
  call-terminated two-call chain — additionally parenthesizes its base receiver so ruff keeps it
  fluent (`(resolved)`, `(element.page)`); a multiline argument on a step is kept intact and
  re-indented, and chains inside f-string interpolations are exempt
- the fixer is the anchor's only writer: it emits the anchor when exploding a chain and strips
  one that is stale (its chain shrank below the threshold) or mislaid (re-anchored by the next
  pass), so the directive cannot rot; anchor matching is exact — any other comment text is a
  foreign comment, never touched, and a chain carrying one is reported for human layout
- the pairing order stays actually-then-ruff: the anchored layout is a fixpoint of
  `actually format` followed by `ruff format` under the recommended config

## Consequences

- the wanted state is a deliberate, temporary middle-ground — multiline as far as ruff preserves
  without fighting the formatter, not the one-node-per-line ideal: an attribute between two calls
  rides with its call and a short chain keeps its base parens, because ruff re-joins them
  otherwise, and `ruff format` exposes no per-behavior toggle to relax it. A ruff-incompatible
  mode was considered and rejected: it would fight the formatter and oscillate under any later
  `ruff format`
- the first rule whose fix emits and removes comments; the anchor is a machine-managed tool
  directive, not prose — consumers with zero-comment policies classify it with their other tool
  directives (`# noqa`, `# shellcheck`)
- a near-miss spelling of the anchor is a foreign comment: it blocks the auto-fix and surfaces
  as a reported violation instead of silently half-working
- a native ruff fluent-chain option would retire the anchor mechanism; per ADR 2 that semantics
  change ships as a new rule code, with ACTH001 going `removed`
