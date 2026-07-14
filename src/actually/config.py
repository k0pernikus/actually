import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from actually.violations import (
    ALL_GROUP,
    ALL_RULE_CODES,
    RULE_SELECTOR_BY_VALUE,
    RULES,
    RuleCode,
    RuleSelector,
)


CONFIG_FILE_NAME = "well-actually.toml"
KNOWN_CONFIG_KEYS = frozenset(
    {
        "exclude",
        "include",
    },
)


class SelectionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class LoadedSelection:
    enabled: frozenset[RuleCode]
    config_file_found: bool


def load_selection(
    work_dir: Path,
    cli_include: tuple[str, ...],
    cli_exclude: tuple[str, ...],
) -> LoadedSelection:
    candidate = work_dir / CONFIG_FILE_NAME
    file_include, file_exclude = _parse_config(candidate) if candidate.is_file() else ((), ())
    include = cli_include if cli_include else file_include
    exclude = cli_exclude if cli_exclude else file_exclude

    return LoadedSelection(
        enabled=resolve_selection(include, exclude),
        config_file_found=candidate.is_file(),
    )


def describe_selection(enabled: frozenset[RuleCode]) -> str:
    if enabled == ALL_RULE_CODES:
        return ALL_GROUP

    excluded = ALL_RULE_CODES - enabled
    if len(excluded) < len(enabled):
        return f"{ALL_GROUP} except {', '.join(sorted(excluded))}"

    return ", ".join(sorted(enabled))


def selection_declaration(enabled: frozenset[RuleCode], *, config_file_found: bool) -> str:
    description = describe_selection(enabled)
    match config_file_found, description == ALL_GROUP:
        case True, _:
            return f"Found {CONFIG_FILE_NAME}. Running with: {description}"

        case _, True:
            return f"No {CONFIG_FILE_NAME} found, running with default '{ALL_GROUP}'"

        case _:
            return f"No {CONFIG_FILE_NAME} found, running with: {description}"


def resolve_selection(
    include: tuple[str, ...],
    exclude: tuple[str, ...],
) -> frozenset[RuleCode]:
    include_selectors = _narrowed(include)
    exclude_selectors = _narrowed(exclude)
    _reject_repeated_selectors(include_selectors, exclude_selectors)
    effective_include = _effective_include(include_selectors, exclude_selectors)
    enabled = frozenset(rule.code for rule in RULES if _match_length(rule.code, effective_include) > _match_length(rule.code, exclude_selectors))
    if not enabled:
        raise SelectionError("selection enables no rules — include at least one rule code or prefix")

    return enabled


def _narrowed(entries: tuple[str, ...]) -> tuple[RuleSelector, ...]:
    return tuple(_narrowed_entry(entry) for entry in entries)


def _narrowed_entry(entry: str) -> RuleSelector:
    selector = RULE_SELECTOR_BY_VALUE.get(entry)
    if selector is None:
        raise SelectionError(f"unknown rule selector {entry!r} — valid: {sorted(RULE_SELECTOR_BY_VALUE)}")

    return selector


def _reject_repeated_selectors(
    include: tuple[RuleSelector, ...],
    exclude: tuple[RuleSelector, ...],
) -> None:
    counts = Counter((*include, *exclude))
    repeated = sorted(entry for entry, count in counts.items() if count > 1)
    if repeated:
        raise SelectionError(f"a selector may appear at most once across include and exclude — repeated: {', '.join(repeated)}")


def _effective_include(
    include: tuple[RuleSelector, ...],
    exclude: tuple[RuleSelector, ...],
) -> tuple[RuleSelector, ...]:
    if include:
        return include

    if ALL_GROUP in exclude:
        raise SelectionError(f"exclude = {ALL_GROUP} requires at least one include entry")

    return (ALL_GROUP,)


def _match_length(code: RuleCode, entries: tuple[RuleSelector, ...]) -> int:
    if not entries:
        return -1

    return max(_entry_match_length(code, entry) for entry in entries)


def _entry_match_length(code: RuleCode, entry: RuleSelector) -> int:
    if entry == ALL_GROUP:
        return 0

    if code.startswith(entry):
        return len(entry)

    return -1


def _parse_config(path: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    unknown = set(payload) - KNOWN_CONFIG_KEYS
    if unknown:
        raise SelectionError(f"{path}: unknown keys {sorted(unknown)} — valid: {sorted(KNOWN_CONFIG_KEYS)}")

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
