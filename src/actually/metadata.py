import tomllib
from dataclasses import dataclass
from importlib.resources import files
from typing import Literal

from actually.violations import RULES, Rule, RuleCode, RuleGroup, RuleName


RULES_TOML_RESOURCE = "rules.toml"
RULE_DOCS_BASE_URL = "https://github.com/k0pernikus/actually/blob/main/rules"

ActiveStatus = Literal["stable", "unstable"]
FixCapability = Literal["check-only", "full", "partial"]

STATUS_VALUES = frozenset(
    {
        "removed",
        "stable",
        "unstable",
    },
)
DECLARABLE_FIX_VALUES = frozenset(
    {
        "full",
        "partial",
    },
)
ACTIVE_RULE_KEYS = frozenset(
    {
        "banned",
        "code",
        "fix",
        "group",
        "name",
        "rationale",
        "status",
        "summary",
        "wanted",
    },
)
RETIRED_RULE_KEYS = frozenset(
    {
        "code",
        "group",
        "name",
        "status",
    },
)

FIX_LABELS: dict[FixCapability, str] = {
    "check-only": "no",
    "full": "yes",
    "partial": "partial",
}


@dataclass(frozen=True, slots=True)
class RuleMetadata:
    code: RuleCode
    name: RuleName
    group: RuleGroup
    status: ActiveStatus
    fix: FixCapability
    summary: str
    rationale: str
    banned: str
    wanted: str


@dataclass(frozen=True, slots=True)
class RetiredRuleMetadata:
    code: str
    name: str
    group: str


@dataclass(frozen=True, slots=True)
class RuleCatalog:
    active: tuple[RuleMetadata, ...]
    retired: tuple[RetiredRuleMetadata, ...]


def rule_docs_url(name: RuleName) -> str:
    return f"{RULE_DOCS_BASE_URL}/{name}.md"


def load_rule_catalog() -> RuleCatalog:
    payload = tomllib.loads(files("actually").joinpath(RULES_TOML_RESOURCE).read_text(encoding="utf-8"))
    entries = payload.get("rules")
    if not isinstance(entries, list):
        raise TypeError("rules.toml must declare an array of [[rules]] tables")

    active: list[RuleMetadata] = []
    retired: list[RetiredRuleMetadata] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise TypeError("every [[rules]] entry must be a table")

        status = _validated_status(entry)
        if status == "removed":
            retired.append(_retired_rule(entry))
            continue

        active.append(_active_rule(entry, status))

    catalog = RuleCatalog(active=tuple(active), retired=tuple(retired))
    _reject_duplicates(
        [
            *(rule.code for rule in catalog.active),
            *(rule.code for rule in catalog.retired),
        ],
        "code",
    )
    _reject_duplicates(
        [
            *(rule.name for rule in catalog.active),
            *(rule.name for rule in catalog.retired),
        ],
        "name",
    )
    _validate_registry_congruence(catalog)

    return catalog


def _validated_status(
    entry: dict[str, object],
) -> Literal["removed", "stable", "unstable"]:
    status = entry.get("status")
    if status == "removed":
        return "removed"

    if status == "stable":
        return "stable"

    if status == "unstable":
        return "unstable"

    raise ValueError(f"invalid status {status!r} — allowed: {sorted(STATUS_VALUES)}")


def _active_rule(entry: dict[str, object], status: ActiveStatus) -> RuleMetadata:
    _reject_unknown_keys(entry, ACTIVE_RULE_KEYS)
    registered = _registered_rule(_required_string(entry, "code"))
    _reject_field_drift(entry, "name", registered.name)
    _reject_field_drift(entry, "group", registered.group)

    return RuleMetadata(
        code=registered.code,
        name=registered.name,
        group=registered.group,
        status=status,
        fix=_fix_capability(entry),
        summary=_required_string(entry, "summary"),
        rationale=_required_string(entry, "rationale"),
        banned=_required_string(entry, "banned"),
        wanted=_required_string(entry, "wanted"),
    )


def _registered_rule(code: str) -> Rule:
    for rule in RULES:
        if rule.code == code:
            return rule

    raise ValueError(f"rules.toml entry {code!r} is not in the code registry")


def _reject_field_drift(entry: dict[str, object], key: str, registered: str) -> None:
    declared = _required_string(entry, key)
    if declared != registered:
        raise ValueError(f"rules.toml {key} {declared!r} does not match the registry {registered!r}")


def _retired_rule(entry: dict[str, object]) -> RetiredRuleMetadata:
    _reject_unknown_keys(entry, RETIRED_RULE_KEYS)

    return RetiredRuleMetadata(
        code=_required_string(entry, "code"),
        name=_required_string(entry, "name"),
        group=_required_string(entry, "group"),
    )


def _fix_capability(entry: dict[str, object]) -> FixCapability:
    if "fix" not in entry:
        return "check-only"

    fix = entry["fix"]
    if fix == "full":
        return "full"

    if fix == "partial":
        return "partial"

    raise ValueError(f"invalid fix {fix!r} — declare one of {sorted(DECLARABLE_FIX_VALUES)} or omit the key")


def _reject_unknown_keys(entry: dict[str, object], allowed: frozenset[str]) -> None:
    unknown = set(entry) - allowed
    if unknown:
        raise ValueError(f"unknown keys in a [[rules]] entry: {sorted(unknown)}")


def _reject_duplicates(values: list[str], label: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"duplicate {label} in rules.toml")


def _required_string(entry: dict[str, object], key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or empty string for {key!r} in a [[rules]] entry")

    return value.strip()


def _validate_registry_congruence(catalog: RuleCatalog) -> None:
    documented = {rule.code for rule in catalog.active}
    registered = {rule.code for rule in RULES}
    if documented != registered:
        raise ValueError(f"rules.toml documents {sorted(documented)} but the code registry holds {sorted(registered)}")

    still_implemented = {rule.code for rule in catalog.retired} & {str(code) for code in registered}
    if still_implemented:
        raise ValueError(f"removed rules still present in the code registry: {sorted(still_implemented)}")
