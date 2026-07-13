import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import rich_click as click

from actually.checks import find_violations
from actually.violations import RULES, Rule

REPO_ROOT = Path(__file__).resolve().parent.parent
RULES_TOML_PATH = REPO_ROOT / "rules.toml"
TEMPLATE_PATH = REPO_ROOT / "README.template.md"
README_PATH = REPO_ROOT / "README.md"
RULES_DIR = REPO_ROOT / "rules"
PLACEHOLDER = "{{rules_table}}"

ActiveStatus = Literal["stable", "unstable"]
FixCapability = Literal["check-only", "full", "partial"]

STATUS_VALUES = frozenset(
    {
        "removed",
        "stable",
        "unstable",
    }
)
DECLARABLE_FIX_VALUES = frozenset(
    {
        "full",
        "partial",
    }
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
    }
)
RETIRED_RULE_KEYS = frozenset(
    {
        "code",
        "group",
        "name",
        "status",
    }
)

FIX_LABELS = {
    "check-only": "no",
    "full": "yes",
    "partial": "partial",
}

PAGE_NOTICE = (
    "Generated from [`rules.toml`](../rules.toml) by"
    " [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file."
)


@dataclass(frozen=True, slots=True)
class ActiveRule:
    code: str
    name: str
    group: str
    status: ActiveStatus
    fix: FixCapability
    summary: str
    rationale: str
    banned: str
    wanted: str


@dataclass(frozen=True, slots=True)
class RetiredRule:
    code: str
    name: str
    group: str


@click.command(
    help="Generate README.md and rules/*.md from README.template.md and rules.toml."
)
@click.option(
    "--check",
    "check_only",
    is_flag=True,
    help="Exit 1 when any generated doc is stale or stray instead of writing.",
)
def main(check_only: bool) -> None:
    active, retired = _load_rules()
    _validate_registry_congruence(active, retired)
    for rule in active:
        _validate_snippets(rule)

    rendered_readme = _render_readme(active, retired)
    pages = {RULES_DIR / f"{rule.name}.md": _render_rule_page(rule) for rule in active}
    if check_only:
        _assert_fresh(rendered_readme, pages)
        click.echo("generated docs are fresh")

        return

    _write_outputs(rendered_readme, pages)
    click.echo(f"wrote README.md and {len(pages)} rule pages")


def _load_rules() -> tuple[tuple[ActiveRule, ...], tuple[RetiredRule, ...]]:
    payload = tomllib.loads(RULES_TOML_PATH.read_text(encoding="utf-8"))
    entries = payload.get("rules")
    if not isinstance(entries, list):
        raise ValueError("rules.toml must declare an array of [[rules]] tables")

    active: list[ActiveRule] = []
    retired: list[RetiredRule] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("every [[rules]] entry must be a table")

        status = _validated_status(entry)
        if status == "removed":
            retired.append(_retired_rule(entry))
            continue

        active.append(_active_rule(entry, status))

    _reject_duplicates(
        [
            *(rule.code for rule in active),
            *(rule.code for rule in retired),
        ],
        "code",
    )
    _reject_duplicates(
        [
            *(rule.name for rule in active),
            *(rule.name for rule in retired),
        ],
        "name",
    )

    return (tuple(active), tuple(retired))


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


def _active_rule(entry: dict[str, object], status: ActiveStatus) -> ActiveRule:
    _reject_unknown_keys(entry, ACTIVE_RULE_KEYS)

    return ActiveRule(
        code=_required_string(entry, "code"),
        name=_required_string(entry, "name"),
        group=_required_string(entry, "group"),
        status=status,
        fix=_fix_capability(entry),
        summary=_required_string(entry, "summary"),
        rationale=_required_string(entry, "rationale"),
        banned=_required_string(entry, "banned"),
        wanted=_required_string(entry, "wanted"),
    )


def _retired_rule(entry: dict[str, object]) -> RetiredRule:
    _reject_unknown_keys(entry, RETIRED_RULE_KEYS)

    return RetiredRule(
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

    raise ValueError(
        f"invalid fix {fix!r} — declare one of {sorted(DECLARABLE_FIX_VALUES)} or omit the key"
    )


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


def _validate_registry_congruence(
    active: tuple[ActiveRule, ...], retired: tuple[RetiredRule, ...]
) -> None:
    registry: dict[str, Rule] = {rule.code: rule for rule in RULES}
    documented = {rule.code for rule in active}
    if documented != set(registry):
        raise ValueError(
            f"rules.toml documents {sorted(documented)} but the code registry holds {sorted(registry)}"
        )

    still_implemented = {rule.code for rule in retired} & set(registry)
    if still_implemented:
        raise ValueError(
            f"removed rules still present in the code registry: {sorted(still_implemented)}"
        )

    for rule in active:
        registered = registry[rule.code]
        if (rule.name, rule.group) != (registered.name, registered.group):
            raise ValueError(
                f"{rule.code}: rules.toml says ({rule.name}, {rule.group}),"
                f" the registry says ({registered.name}, {registered.group})",
            )


def _validate_snippets(rule: ActiveRule) -> None:
    triggered = {violation.rule.code for violation in find_violations(rule.banned)}
    if rule.code not in triggered:
        raise ValueError(
            f"{rule.code}: the banned example does not trigger the rule (triggered: {sorted(triggered)})"
        )

    remaining = find_violations(rule.wanted)
    if remaining:
        details = ", ".join(
            f"{violation.rule.code}@{violation.line}" for violation in remaining
        )
        raise ValueError(f"{rule.code}: the wanted example is not clean ({details})")


def _render_readme(
    active: tuple[ActiveRule, ...], retired: tuple[RetiredRule, ...]
) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise ValueError(f"placeholder {PLACEHOLDER} missing from README.template.md")

    return template.replace(PLACEHOLDER, _render_rules_table(active, retired))


def _render_rules_table(
    active: tuple[ActiveRule, ...], retired: tuple[RetiredRule, ...]
) -> str:
    lines = [
        "| Code | Rule | Status | Auto-fix | What it enforces |",
        "|:---|:---|:---|:---|:---|",
        *(
            f"| {rule.code} | [{rule.name}](rules/{rule.name}.md) | {rule.status} | {FIX_LABELS[rule.fix]} | {rule.summary} |"
            for rule in sorted(active, key=lambda rule: rule.code)
        ),
    ]
    if retired:
        names = ", ".join(
            f"{rule.code} ({rule.name})"
            for rule in sorted(retired, key=lambda rule: rule.code)
        )
        lines.extend(
            [
                "",
                f"Retired codes, never recycled: {names}.",
            ]
        )

    return "\n".join(lines)


def _render_rule_page(rule: ActiveRule) -> str:
    parts = [
        f"# {rule.code} — {rule.name}",
        "",
        f"**Group:** {rule.group}",
        f"**Status:** {rule.status}",
        f"**Auto-fix:** {FIX_LABELS[rule.fix]}",
        "",
        rule.rationale,
        "",
        "## Banned",
        "",
        "```python",
        rule.banned,
        "```",
        "",
        "## Wanted",
        "",
        "```python",
        rule.wanted,
        "```",
        "",
        PAGE_NOTICE,
        "",
    ]

    return "\n".join(parts)


def _assert_fresh(rendered_readme: str, pages: dict[Path, str]) -> None:
    problems = _staleness_report(rendered_readme, pages)
    if not problems:
        return

    for problem in problems:
        click.secho(f"stale: {problem}", fg="red", err=True)

    click.secho("run: uv run python scripts/generate_docs.py", fg="red", err=True)
    raise SystemExit(1)


def _staleness_report(rendered_readme: str, pages: dict[Path, str]) -> tuple[str, ...]:
    problems = []
    if (
        not README_PATH.is_file()
        or README_PATH.read_text(encoding="utf-8") != rendered_readme
    ):
        problems.append("README.md")

    for path, content in sorted(pages.items()):
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            problems.append(str(path.relative_to(REPO_ROOT)))

    problems.extend(
        f"{stray.relative_to(REPO_ROOT)} (stray)" for stray in _stray_pages(pages)
    )

    return tuple(problems)


def _stray_pages(pages: dict[Path, str]) -> tuple[Path, ...]:
    if not RULES_DIR.is_dir():
        return ()

    return tuple(sorted(path for path in RULES_DIR.glob("*.md") if path not in pages))


def _write_outputs(rendered_readme: str, pages: dict[Path, str]) -> None:
    README_PATH.write_text(rendered_readme, encoding="utf-8")
    RULES_DIR.mkdir(exist_ok=True)
    for path, content in sorted(pages.items()):
        path.write_text(content, encoding="utf-8")

    for stray in _stray_pages(pages):
        stray.unlink()


if __name__ == "__main__":
    main()
