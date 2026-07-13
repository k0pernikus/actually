# actually

Well, *actually*, your code should read like this.

`actually` is a highly opinionated Python linter and formatter built on
[ast-grep](https://ast-grep.github.io/). It enforces a guard-clause style through rules with
ruff-style stable codes, grouped by language construct
([ADR 1](docs/decisions/1_ruff_style_rule_codes_in_named_groups.md)). Every rule is checkable;
the auto-fix column marks what `format` can rewrite. Each rule links to its documentation page
with rationale and a banned/wanted example pair — generated from
[`rules.toml`](src/actually/rules.toml) and validated by the linter itself
([ADR 2](docs/decisions/2_rule_docs_generated_from_rules_toml.md)). `actually rules --list`
prints the same catalog in the terminal, docs links included:

{{rules_tables}}

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

`check` reports violations and exits non-zero when it finds any. Both commands lint `.py`
files only; directory scans skip environment, cache, and VCS directories (`.venv`, `venv`,
`.git`, `__pycache__`, `node_modules`, and friends) and respect `.gitignore` files — nested
ones and negations included, matched via [pathspec](https://pypi.org/project/pathspec/)
(black's approach), so no git installation is required. When a `.git` directory is found
above the scanned path, `.gitignore` files up to that repo root apply as well. Global
excludes (`core.excludesFile`, `.git/info/exclude`) are not consulted. A `.py` file passed
explicitly is always linted.

`format` rewrites files in place, then reports what it could not fix:

- inserts the missing blank lines around `return`
- dedents a `try/except/else` completion clause into straight-line code when every `except`
  body already exits (`return`, `raise`, `continue`, `break`) — when one falls through, the
  rewrite would change behaviour, so it is reported for human refactoring instead
- rewrites dict/list/set literals to one element per line with a trailing comma — literals
  carrying comments or multiline elements are reported for human formatting instead
- `--only-autofixable` makes it best effort: every available fix is applied, the remaining
  violations are still reported, and the exit code stays 0

## Configuration

Select the rule subset in a `well-actually.toml` (sourced from the current working directory
only — never a parent) or with repeatable `--include` / `--exclude` options, which override
the file's corresponding list
([ADR 5](docs/decisions/5_rule_selection_by_prefix_specificity.md)). Every invocation
declares its selection on stderr — `Found well-actually.toml. Running with: …` or
`No well-actually.toml found, running with default '__ALL__'` — so the active subset is
never a matter of guessing.
Entries are rule codes (`ACTC004`), group prefixes (`ACTC`), or `__ALL__` — the special
all-encompassing group ([ADR 6](docs/decisions/6_selector_taxonomy_rule_group_all.md)). The
longest match per rule wins; ties go to `exclude`. `include` defaults to `__ALL__`, so
exclude-only configs just work:

```toml
exclude = ["ACTL"]
```

Any subset is expressible — one rule only:

```toml
exclude = ["__ALL__"]
include = ["ACTC004"]
```

or a group off with one member kept:

```toml
exclude = ["ACTL"]
include = ["__ALL__", "ACTL001"]
```

Hard errors instead of silent tolerance: an unknown selector, `__ALL__` appearing more than
once across both lists, `exclude = ["__ALL__"]` without any include entry, and a selection
that enables no rules. `format` obeys the selection — a disabled rule neither reports nor
fixes.

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
