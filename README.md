# actually

Well, *actually*, your code should read like this.

`actually` is a highly opinionated Python linter and formatter built on
[ast-grep](https://ast-grep.github.io/). It enforces a guard-clause style:

- `else` is banned — on `if`, and as the completion clause on `for`, `while`, and `try` alike
- `elif` is banned
- ternaries are allowed only flat — nested conditional expressions are banned
- `return` needs a blank line above it when it follows other statements in its block
- `return` needs a blank line below it when more code follows

## Usage

```bash
uvx well-actually check src/
uvx well-actually format src/
```

Installed (`uv tool install well-actually`), the short command is available too:

```bash
actually check src/
actually format src/
```

`check` reports violations and exits non-zero when it finds any.

`format` rewrites files in place, then reports what it could not fix:

- inserts the missing blank lines around `return`
- dedents a `try/except/else` completion clause into straight-line code when every `except`
  body already exits (`return`, `raise`, `continue`, `break`) — when one falls through, the
  rewrite would change behaviour, so it is reported for human refactoring instead

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
uv run pytest
uv run actually check src/ tests/
```
