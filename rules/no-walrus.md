<!-- GENERATED FILE — DO NOT EDIT. Hand edits are overwritten by the pre-commit hook; edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->
# ACTO001 — no-walrus

**Group:** actually-operators
**Status:** stable
**Auto-fix:** no

A statement acts — it binds a name or changes state; an expression only computes a value. The
walrus operator `:=` erases that line, binding a name as a side effect of evaluating a larger
expression, so a reader scanning for where a name is defined must now look inside conditions,
comprehensions, and boolean operands. Keep the line hard: data flows top-to-bottom, every name
defined on its own statement above its first use.

## Bind above the use, not mid-condition

A name is defined on its own statement above its first use — `n = len(data)` then `if n > 10:`,
never folded into the condition it feeds.

### Banned

```python
if (n := len(data)) > 10:
    process(data)
```

### Wanted

```python
n = len(data)
if n > 10:
    process(data)
```

## Short-circuit hides which calls run

The cost compounds when a condition short-circuits over side-effecting calls. Take a probe that
counts how often each method runs:

```python
class Probe:
    def __init__(self) -> None:
        self.f_runs = 0
        self.g_runs = 0

    def f(self) -> int:
        self.f_runs += 1

        return 0

    def g(self, x: int) -> int:
        self.g_runs += 1

        return 42
```

`if (x := probe.f()) and (y := probe.g(x)):` runs `g` only when `x` is truthy — `and`
short-circuits, so a falsy `x` leaves `g` unrun and `g_runs` at zero. Yet a reader skimming the
line parses it as three plain statements — `x = probe.f()`, `y = probe.g(x)`, `if x and y:` —
which would call `g` unconditionally: a different program. Guard clauses make the control flow the
eye already expects — bind, check, exit — one decision per statement, the short-circuit now
explicit as an early return.

### Banned

```python
def check(probe):
    if (x := probe.f()) and (y := probe.g(x)):
        return
```

### Wanted

```python
def check(probe):
    x = probe.f()
    if not x:
        return

    y = probe.g(x)
    if not y:
        return
```

Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file.
