import tomllib
from pathlib import Path

from actually.violations import (
    RULE_SELECTOR_BY_VALUE,
    RULES,
    RuleCode,
    RuleSelector,
)

ALL_SENTINEL: RuleSelector = "__ALL__"
CONFIG_FILE_NAME = "well-actually.toml"
KNOWN_CONFIG_KEYS = frozenset(
    {
        "exclude",
        "include",
    },
)


class SelectionError(ValueError):
    pass


def load_selection(
    start_dir: Path,
    cli_include: tuple[str, ...],
    cli_exclude: tuple[str, ...],
) -> frozenset[RuleCode]:
    file_include, file_exclude = _config_file_lists(start_dir)
    include = cli_include if cli_include else file_include
    exclude = cli_exclude if cli_exclude else file_exclude

    return resolve_selection(include, exclude)


def resolve_selection(
    include: tuple[str, ...],
    exclude: tuple[str, ...],
) -> frozenset[RuleCode]:
    include_selectors = _narrowed(include)
    exclude_selectors = _narrowed(exclude)
    _reject_repeated_all(include_selectors, exclude_selectors)
    effective_include = _effective_include(include_selectors, exclude_selectors)
    enabled = frozenset(
        rule.code
        for rule in RULES
        if _match_length(rule.code, effective_include)
        > _match_length(rule.code, exclude_selectors)
    )
    if not enabled:
        raise SelectionError(
            "selection enables no rules — include at least one rule code or prefix"
        )

    return enabled


def _narrowed(entries: tuple[str, ...]) -> tuple[RuleSelector, ...]:
    return tuple(_narrowed_entry(entry) for entry in entries)


def _narrowed_entry(entry: str) -> RuleSelector:
    selector = RULE_SELECTOR_BY_VALUE.get(entry)
    if selector is None:
        raise SelectionError(
            f"unknown rule selector {entry!r} — valid: {sorted(RULE_SELECTOR_BY_VALUE)}"
        )

    return selector


def _reject_repeated_all(
    include: tuple[RuleSelector, ...],
    exclude: tuple[RuleSelector, ...],
) -> None:
    occurrences = sum(1 for entry in (*include, *exclude) if entry == ALL_SENTINEL)
    if occurrences > 1:
        raise SelectionError(
            f"{ALL_SENTINEL} may appear at most once across include and exclude"
        )


def _effective_include(
    include: tuple[RuleSelector, ...],
    exclude: tuple[RuleSelector, ...],
) -> tuple[RuleSelector, ...]:
    if include:
        return include

    if ALL_SENTINEL in exclude:
        raise SelectionError(
            f"exclude = {ALL_SENTINEL} requires at least one include entry"
        )

    return (ALL_SENTINEL,)


def _match_length(code: RuleCode, entries: tuple[RuleSelector, ...]) -> int:
    if not entries:
        return -1

    return max(_entry_match_length(code, entry) for entry in entries)


def _entry_match_length(code: RuleCode, entry: RuleSelector) -> int:
    if entry == ALL_SENTINEL:
        return 0

    if code.startswith(entry):
        return len(entry)

    return -1


def _config_file_lists(start_dir: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    for directory in (start_dir, *start_dir.resolve().parents):
        candidate = directory / CONFIG_FILE_NAME
        if candidate.is_file():
            return _parse_config(candidate)

    return ((), ())


def _parse_config(path: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    unknown = set(payload) - KNOWN_CONFIG_KEYS
    if unknown:
        raise SelectionError(
            f"{path}: unknown keys {sorted(unknown)} — valid: {sorted(KNOWN_CONFIG_KEYS)}"
        )

    return (
        _string_tuple(payload, "include", path),
        _string_tuple(payload, "exclude", path),
    )


def _string_tuple(payload: dict[str, object], key: str, path: Path) -> tuple[str, ...]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        raise SelectionError(f"{path}: {key} must be an array of strings")

    return tuple(_string_entry(entry, key, path) for entry in value)


def _string_entry(entry: object, key: str, path: Path) -> str:
    if not isinstance(entry, str):
        raise SelectionError(f"{path}: {key} must be an array of strings")

    return entry
