from pathlib import Path

import rich_click as click

from actually.checks import find_violations
from actually.metadata import (
    FIX_LABELS,
    RetiredRuleMetadata,
    RuleCatalog,
    RuleExample,
    RuleMetadata,
    load_rule_catalog,
)
from actually.suppressions import banned_violations
from actually.violations import Violation


REPO_ROOT = (
    Path(__file__)  # well-actually: multi-line
    .resolve()
    .parent.parent
)
TEMPLATE_PATH = REPO_ROOT / "README.template.md"
README_PATH = REPO_ROOT / "README.md"
RULES_DIR = REPO_ROOT / "rules"
PLACEHOLDER = "{{rules_tables}}"
READONLY_MODE = 0o444
WRITABLE_MODE = 0o644

GENERATED_BANNER = (
    "<!-- GENERATED FILE — DO NOT EDIT."
    " Hand edits are overwritten by the pre-commit hook;"
    " edit README.template.md / src/actually/rules.toml and run:  uv run python scripts/generate_docs.py -->"
)

PAGE_NOTICE = "Generated from [`rules.toml`](../src/actually/rules.toml) by [`scripts/generate_docs.py`](../scripts/generate_docs.py) — edit the TOML, not this file."


@click.command(help="Generate README.md and rules/*.md from README.template.md and src/actually/rules.toml.")
@click.option(
    "--check",
    "check_only",
    is_flag=True,
    help="Exit 1 when any generated doc is stale or stray instead of writing.",
)
def main(check_only: bool) -> None:
    catalog = load_rule_catalog()
    for rule in catalog.active:
        _validate_snippets(rule)

    rendered_readme = _render_readme(catalog)
    pages = {RULES_DIR / f"{rule.name}.md": _render_rule_page(rule) for rule in catalog.active}
    if check_only:
        _assert_fresh(rendered_readme, pages)
        click.echo("generated docs are fresh")

        return

    _write_outputs(rendered_readme, pages)
    click.echo(f"wrote README.md and {len(pages)} rule pages")


def _validate_snippets(rule: RuleMetadata) -> None:
    for example in rule.examples:
        _validate_example(rule, example)


def _triggered(source: str, banned_noqa: tuple[str, ...]) -> tuple[Violation, ...]:
    return (
        *find_violations(source),
        *banned_violations(source, banned_noqa),
    )


def _validate_example(rule: RuleMetadata, example: RuleExample) -> None:
    triggered = {violation.rule.code for violation in _triggered(example.banned, example.banned_noqa)}
    if rule.code not in triggered:
        raise ValueError(f"{rule.code} example {example.title!r}: banned does not trigger the rule (triggered: {sorted(triggered)})")

    remaining = _triggered(example.wanted, example.banned_noqa)
    if remaining:
        details = ", ".join(f"{violation.rule.code}@{violation.line}" for violation in remaining)
        raise ValueError(f"{rule.code} example {example.title!r}: wanted is not clean ({details})")


def _render_readme(catalog: RuleCatalog) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise ValueError(f"placeholder {PLACEHOLDER} missing from README.template.md")

    rendered = template.replace(PLACEHOLDER, _render_group_tables(catalog))

    return f"{GENERATED_BANNER}\n{rendered}"


def _render_group_tables(catalog: RuleCatalog) -> str:
    groups = sorted({rule.group for rule in catalog.active})
    sections = [
        _render_group_section(
            group,
            tuple(rule for rule in catalog.active if rule.group == group),
        )
        for group in groups
    ]
    if catalog.retired:
        names = ", ".join(f"{rule.code} ({rule.name})" for rule in sorted(catalog.retired, key=_retired_sort_key))
        sections.append(f"Retired codes, never recycled: {names}.")

    return "\n\n".join(sections)


def _retired_sort_key(rule: RetiredRuleMetadata) -> str:
    return rule.code


def _render_group_section(group: str, rules: tuple[RuleMetadata, ...]) -> str:
    lines = [
        f"## {group}",
        "",
        "| Code | Rule | Status | Auto-fix | What it enforces |",
        "|:---|:---|:---|:---|:---|",
        *(f"| {rule.code} | [{rule.name}](rules/{rule.name}.md) | {rule.status} | {FIX_LABELS[rule.fix]} | {rule.summary} |" for rule in sorted(rules, key=lambda rule: rule.code)),
    ]

    return "\n".join(lines)


def _render_rule_page(rule: RuleMetadata) -> str:
    parts = [
        GENERATED_BANNER,
        f"# {rule.code} — {rule.name}",
        "",
        f"**Group:** {rule.group}",
        f"**Status:** {rule.status}",
        f"**Auto-fix:** {FIX_LABELS[rule.fix]}",
        "",
        rule.rationale,
        "",
        *_examples_block(rule),
        *_conflicts_block(rule),
        PAGE_NOTICE,
        "",
    ]

    return "\n".join(parts)


def _examples_block(rule: RuleMetadata) -> list[str]:
    return [line for example in rule.examples for line in _example_section(example)]


def _example_section(example: RuleExample) -> list[str]:
    return [
        f"## {example.title}",
        "",
        *_example_rationale(example),
        "### Banned",
        "",
        "```python",
        example.banned,
        "```",
        "",
        "### Wanted",
        "",
        "```python",
        example.wanted,
        "```",
        "",
    ]


def _example_rationale(example: RuleExample) -> list[str]:
    if not example.rationale:
        return []

    return [
        example.rationale,
        "",
    ]


def _conflicts_block(rule: RuleMetadata) -> list[str]:
    return [
        *_relation_section(rule, "conflicts", "Conflicts with ruff"),
        *_relation_section(rule, "supersedes", "Supersedes (stricter than ruff)"),
    ]


def _relation_section(rule: RuleMetadata, kind: str, heading: str) -> list[str]:
    items = [f"- `{conflict.rule}` — {conflict.reason}" for conflict in rule.ruff_conflicts if conflict.kind == kind]
    if not items:
        return []

    return [
        f"## {heading}",
        "",
        *items,
        "",
    ]


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
    if not README_PATH.is_file() or README_PATH.read_text(encoding="utf-8") != rendered_readme:
        problems.append("README.md")

    for path, content in sorted(pages.items()):
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            problems.append(str(path.relative_to(REPO_ROOT)))

    problems.extend(f"{stray.relative_to(REPO_ROOT)} (stray)" for stray in _stray_pages(pages))

    return tuple(problems)


def _stray_pages(pages: dict[Path, str]) -> tuple[Path, ...]:
    if not RULES_DIR.is_dir():
        return ()

    return tuple(sorted(path for path in RULES_DIR.glob("*.md") if path not in pages))


def _write_outputs(rendered_readme: str, pages: dict[Path, str]) -> None:
    _write_readonly(README_PATH, rendered_readme)
    RULES_DIR.mkdir(exist_ok=True)
    for path, content in sorted(pages.items()):
        _write_readonly(path, content)

    for stray in _stray_pages(pages):
        stray.unlink()


def _write_readonly(path: Path, content: str) -> None:
    if path.is_file():
        path.chmod(WRITABLE_MODE)

    path.write_text(content, encoding="utf-8")
    path.chmod(READONLY_MODE)


if __name__ == "__main__":
    main()
