# actually

Well, *actually*, your code should read like this.

`actually` is a highly opinionated Python linter and formatter built on
[ast-grep](https://ast-grep.github.io/). It enforces a guard-clause style through rules with
ruff-style stable codes, grouped by language construct
([ADR 1](docs/decisions/1_ruff_style_rule_codes_in_named_groups.md)). Every rule is checkable;
the auto-fix column marks what `format` can rewrite. Each rule links to its documentation page
with rationale and a banned/wanted example pair — generated from
[`rules.toml`](rules.toml) and validated by the linter itself
([ADR 2](docs/decisions/2_rule_docs_generated_from_rules_toml.md)):

{{rules_table}}

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
- `--only-autofixable` makes it best effort: every available fix is applied, the remaining
  violations are still reported, and the exit code stays 0

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

`README.md` and `rules/*.md` are generated from `README.template.md` and `rules.toml` by
`scripts/generate_docs.py`; an hk pre-commit hook regenerates and stages them. Edit the
sources, never the outputs.
