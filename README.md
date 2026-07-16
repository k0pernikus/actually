<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# actually

Well, *actually*, your code should read like this.

`actually` is a highly opinionated Python linter and formatter built on
[ast-grep](https://ast-grep.github.io/). It enforces a guard-clause style through rules with
ruff-style codes grouped by language construct
([ADR 1](docs/decisions/1_ruff_style_rule_codes_in_named_groups.md)). Every rule is checkable;
the auto-fix column marks what `format` can rewrite. Each rule links to its documentation page
with rationale and a banned/wanted example pair — generated from
[`rules.toml`](src/actually/rules.toml) and validated by the linter itself
([ADR 2](docs/decisions/2_rule_docs_generated_from_rules_toml.md)). `actually rules --list`
prints the same catalog in the terminal, docs links included:

> **Note:** Rule codes, names, and groups are NOT stable while `actually` is pre-1.0 — the
> taxonomy is still being discovered, so any of them may change with breaking changes at will
> ([ADR 11](docs/decisions/11_rule_identifiers_unstable_pre_1_0.md)). Pin a version; do not
> depend on a specific code or name holding across releases.

## actually-chains

| Code | Rule | Status | Auto-fix | What it enforces |
|:---|:---|:---|:---|:---|
| ACTH001 | [multi-line-chain](rules/multi-line-chain.md) | unstable | partial | a chain — two or more method calls, or a method call with a property access — not one call per line under a `# well-actually: multi-line` anchor |

## actually-completion-clauses

| Code | Rule | Status | Auto-fix | What it enforces |
|:---|:---|:---|:---|:---|
| ACTE001 | [no-try-else](rules/no-try-else.md) | stable | partial | `else` on `try` — dedent the continuation after the `except` clauses |
| ACTE002 | [no-for-else](rules/no-for-else.md) | stable | no | `else` on `for` — the loop-completion clause overloads `else` |
| ACTE003 | [no-while-else](rules/no-while-else.md) | stable | no | `else` on `while` — the loop-completion clause overloads `else` |

## actually-if-conditions

| Code | Rule | Status | Auto-fix | What it enforces |
|:---|:---|:---|:---|:---|
| ACTI001 | [no-if-else](rules/no-if-else.md) | stable | no | `else` on an `if` — flatten to guard clauses with early exits |
| ACTI002 | [no-elif](rules/no-elif.md) | stable | no | `elif` — flatten to guard clauses with early exits |
| ACTI003 | [prefer-match](rules/prefer-match.md) | unstable | no | two or more consecutive conditional returns comparing one shared subject, closed by a terminal return or raise — dispatch written as control flow |

## actually-literals

| Code | Rule | Status | Auto-fix | What it enforces |
|:---|:---|:---|:---|:---|
| ACTL001 | [trailing-comma](rules/trailing-comma.md) | unstable | yes | a dict/list/set literal whose last element lacks a trailing comma |
| ACTL002 | [one-element-per-line](rules/one-element-per-line.md) | unstable | partial | a dict/list/set literal with elements sharing a line with a bracket or each other |

## actually-returns

| Code | Rule | Status | Auto-fix | What it enforces |
|:---|:---|:---|:---|:---|
| ACTR001 | [blank-before-return](rules/blank-before-return.md) | stable | yes | a `return` stacked directly under other statements in its block |
| ACTR002 | [blank-after-return](rules/blank-after-return.md) | stable | yes | code directly under a `return` line |

## actually-ternaries

| Code | Rule | Status | Auto-fix | What it enforces |
|:---|:---|:---|:---|:---|
| ACTT001 | [ternary-not-nested](rules/ternary-not-nested.md) | stable | no | a ternary inside another ternary's arm (`elif` in expression form) |
| ACTT002 | [ternary-not-empty](rules/ternary-not-empty.md) | unstable | no | a degenerate ternary arm (`None`, `""`, empty container) — conditional inclusion in disguise |

## Standing on Ruff and Ty

`actually` deliberately covers only what [ruff](https://docs.astral.sh/ruff/) and
[ty](https://github.com/astral-sh/ty) cannot express — they do most of the lifting; adopt
them first. Our recommended configurations are this repo's own [`ruff.toml`](ruff.toml) and
[`ty.toml`](ty.toml). `actually`'s opinionation starts where those stop, and it MANDATES
compatibility of its own output: no `actually` rule demands, and no `actually format` fix
produces, code those rule sets reject — after `actually format`, a `ruff check` under the
recommended configuration is a no-op. `ruff format` is not guaranteed one: an inserted
trailing comma is exactly the magic trailing comma ruff format expands, so a literal
`actually` fixed without exploding still reformats. Run `actually format` before
`ruff format` and let ruff own the final layout. `well-actually` never runs ruff or ty
itself — it is its own tool with neither as a dependency; pair them in your own pipeline,
in that order. This repo gates itself on both toolchains plus its own linter on every
commit, which is the guarantee exercised live.

`format` and `check` divide the work by whether a fix is mechanical
([ADR 12](docs/decisions/12_autofixables_are_mechanical_sanitation.md)). `format` applies every
autofixable violation, prints only the files it changes, stays silent on a no-op, and exits 0 —
mechanical sanitation for a commit hook or CI, never a report a human reads. `check` surfaces what
is left: bare, it reports every violation; `--only-autofixable` narrows to the mechanical set (the
"is it sanitized?" gate), and `--ignore-autofixable` narrows to the violations a human must
resolve — the code-quality report, undrowned by fixables. The two filters are mutually exclusive.

```bash
# sanitize — mechanical, silent, runs in the commit hook / CI with no human in the loop
actually format .
ruff format .

# gate the sanitation — non-zero if any mechanical fix was skipped
actually check --only-autofixable .

# code-quality report — only what a human must resolve, driven to zero over time
actually check --ignore-autofixable .
```

## Usage

```bash
uvx well-actually@latest check .
uvx well-actually@latest format .
```

The `@latest` matters: a bare `uvx well-actually` reuses a cached tool environment and can
silently run an outdated version; `@latest` re-resolves against the index every time.

Installed (`uv tool install well-actually`), the short command is available too:

```bash
actually check .
actually format .
```

`check` reports violations and exits non-zero when it finds any; `--only-autofixable` and
`--ignore-autofixable` (mutually exclusive) scope the report to the mechanical or the manual set.
Both commands lint `.py`
files only; directory scans skip environment, cache, and VCS directories (`.venv`, `venv`,
`.git`, `__pycache__`, `node_modules`, and friends) and respect `.gitignore` files — nested
ones and negations included, matched via [pathspec](https://pypi.org/project/pathspec/)
(black's approach), so no git installation is required. When a `.git` directory is found
above the scanned path, `.gitignore` files up to that repo root apply as well. Global
excludes (`core.excludesFile`, `.git/info/exclude`) are not consulted. A `.py` file passed
explicitly is always linted.

`format` rewrites files in place, printing only the files it changes and staying silent on a
no-op. It:

- inserts the missing blank lines around `return`
- dedents a `try/except/else` completion clause into straight-line code when every `except`
  body already exits (`return`, `raise`, `continue`, `break`) — when one falls through, the
  rewrite would change behaviour, so it is left for `check` instead
- rewrites dict/list/set literals to one element per line with a trailing comma — literals
  carrying comments or multiline elements are left for `check` instead
- rewrites chains of two or more invocations to one call per line, anchored with
  `# well-actually: multi-line` on the base-receiver line so `ruff format` cannot re-join them,
  parenthesizing a short chain's base receiver
  ([ADR 9](docs/decisions/9_anchor_comments_pin_layout_ruff_cannot_express.md)), and strips the
  anchor when its chain shrinks below two invocations — chains carrying foreign comments or
  multiline arguments are left for `check` instead

Whatever `format` leaves unfixed is a non-autofixable violation that `check` reports —
`check --ignore-autofixable` is the report scoped to exactly that set
([ADR 12](docs/decisions/12_autofixables_are_mechanical_sanitation.md)).

## Configuration

Select the rule subset in a `well-actually.toml` (sourced from the current working directory
only — never a parent) or with repeatable `--include` / `--exclude` options, which override
the file's corresponding list
([ADR 5](docs/decisions/5_rule_selection_by_prefix_specificity.md)). Every invocation
declares its selection on stderr — `Found well-actually.toml. Running with: …` or
`No well-actually.toml found, running with default '__ALL__'` — so the active subset is
never a matter of guessing.
`check --help` and `format --help` are rendered against that same selection: the help names
exactly the rules the invocation will enforce — split for `format` by what it can rewrite —
never overselling nor underselling the changeset, whatever order the selection flags and
`--help` are typed in ([ADR 8](docs/decisions/8_help_reflects_the_active_selection.md)).
Entries are rule codes (`ACTT002`), group prefixes (`ACTI`), or `__ALL__` — the special
all-encompassing group ([ADR 6](docs/decisions/6_selector_taxonomy_rule_group_all.md)). The
longest match per rule wins; ties go to `exclude`. `include` defaults to `__ALL__`, so
exclude-only configs just work:

```toml
exclude = ["ACTL"]
```

Any subset is expressible — one rule only:

```toml
exclude = ["__ALL__"]
include = ["ACTT002"]
```

or a group off with one member kept:

```toml
exclude = ["ACTL"]
include = ["__ALL__", "ACTL001"]
```

Hard errors instead of silent tolerance: an unknown selector, any selector appearing more
than once across the two lists, `exclude = ["__ALL__"]` without any include entry, and a
selection that enables no rules. `format` obeys the selection — a disabled rule neither
reports nor fixes.

## CI Reports

`check` emits machine-readable reports via `--output-format`
(`text`/`gitlab`/`github`/`sarif`) and `--output-file`
([ADR 7](docs/decisions/7_ci_report_formats_mirror_ruff.md)). GitLab code quality:

```yaml
actually:
  script:
    - uvx well-actually@latest check --output-format=gitlab --output-file=gl-code-quality-report.json .
  artifacts:
    when: always
    reports:
      codequality: gl-code-quality-report.json
```

GitHub inline annotations need no upload — `--output-format=github` prints workflow commands;
`--output-format=sarif` produces SARIF 2.1.0 for GitHub code scanning or any SARIF consumer.

## Example

```python
def describe_config(path):
    try:
        config = parse_json_file(path)
    except ParseError:
        return "invalid config"
    else:
        return describe(config)
```

`actually format` rewrites this to:

```python
def describe_config(path):
    try:
        config = parse_json_file(path)
    except ParseError:
        return "invalid config"

    return describe(config)
```

## Development

```bash
uv sync
mise install
hk install
uv run pytest
```

`README.md` and `rules/*.md` are generated from `README.template.md` and
`src/actually/rules.toml` by `scripts/generate_docs.py`; an hk pre-commit hook regenerates
and stages them. Edit the sources, never the outputs.

[`tests/valid-code-checks/allowed/`](tests/valid-code-checks/allowed/) holds the valid-case corpora,
one directory per rule selector (`ACTH001/`, `ACTI/`, `__ALL__/` — any selector
[ADR 6](docs/decisions/6_selector_taxonomy_rule_group_all.md) registers): real Python files the
checker MUST stay silent on and `format` MUST leave byte-identical under exactly that selection.
A per-rule directory pins its rule's allowed shapes atomically, against that rule alone; `__ALL__/` pins the
composed behaviour of the whole rule set in its fixed fixer order
([ADR 10](docs/decisions/10_valid_case_corpora_are_per_selector.md)). The test module beside the
corpora globs the directories, so pinning a new allowed shape is adding a file — no test wiring.
Mutate only via `mise run format-valid-cases`.
