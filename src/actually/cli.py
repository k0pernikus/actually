from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.table import Table

from actually.checks import find_violations
from actually.config import (
    CONFIG_FILE_NAME,
    LoadedSelection,
    SelectionError,
    describe_selection,
    load_selection,
)
from actually.discovery import python_files
from actually.formatting import format_source
from actually.metadata import (
    FIX_LABELS,
    RuleCatalog,
    RuleMetadata,
    load_rule_catalog,
    rule_docs_url,
)
from actually.violations import ALL_GROUP, RuleCode

click.rich_click.COMMAND_GROUPS = {
    "*": [
        {
            "name": "Linting",
            "commands": [
                "check",
                "format",
            ],
        },
        {
            "name": "Rules",
            "commands": [
                "rules",
            ],
        },
    ],
}


@click.group(
    help="Well, actually — an opinionated Python linter: no else, no elif, flat ternaries only, breathing room around return.",
    context_settings={
        "help_option_names": [
            "-h",
            "--help",
        ],
    },
)
@click.version_option(package_name="well-actually")
def main() -> None:
    pass


@main.command(
    name="rules",
    help="Inspect the rule set.",
)
@click.option(
    "--list",
    "list_rules",
    is_flag=True,
    help="List every rule: one table per group with code, name, summary, auto-fix, and docs link.",
)
@click.pass_context
def rules_command(ctx: click.Context, list_rules: bool) -> None:
    if not list_rules:
        click.echo(ctx.get_help())

        return

    console = Console()
    catalog = load_rule_catalog()
    for table in _rule_tables(catalog):
        console.print(table)


def _rule_tables(catalog: RuleCatalog) -> tuple[Table, ...]:
    groups = sorted({rule.group for rule in catalog.active})

    return tuple(
        _group_table(
            group,
            tuple(rule for rule in catalog.active if rule.group == group),
        )
        for group in groups
    )


def _group_table(group: str, rules: tuple[RuleMetadata, ...]) -> Table:
    table = Table(
        title=group,
        title_style="bold",
        header_style="bold",
    )
    table.add_column("Code", style="bold cyan", no_wrap=True)
    table.add_column("Rule", style="magenta", no_wrap=True)
    table.add_column("Enforces")
    table.add_column("Auto-fix", no_wrap=True)
    table.add_column("Docs", style="dim", overflow="fold")
    for rule in sorted(rules, key=_rule_sort_key):
        table.add_row(
            rule.code,
            rule.name,
            rule.summary,
            _fix_cell(rule),
            rule_docs_url(rule.name),
        )

    return table


def _rule_sort_key(rule: RuleMetadata) -> str:
    return rule.code


def _fix_cell(rule: RuleMetadata) -> str:
    styles = {
        "full": "green",
        "partial": "yellow",
        "check-only": "default",
    }

    return f"[{styles[rule.fix]}]{FIX_LABELS[rule.fix]}[/]"


@main.command(
    name="check",
    help="Report violations without modifying files; exit 1 when any are found.",
)
@click.option(
    "--include",
    "include_entries",
    multiple=True,
    help="Rule code, group prefix, or __ALL__; repeatable. Overrides the config file's include list.",
)
@click.option(
    "--exclude",
    "exclude_entries",
    multiple=True,
    help="Rule code, group prefix, or __ALL__; repeatable. Overrides the config file's exclude list.",
)
@click.argument(
    "paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path)
)
def check(
    paths: tuple[Path, ...],
    include_entries: tuple[str, ...],
    exclude_entries: tuple[str, ...],
) -> None:
    enabled = _selection(include_entries, exclude_entries)
    if _report_files(paths, apply_fixes=False, enabled=enabled):
        raise SystemExit(1)


@main.command(
    name="format",
    help="Insert missing blank lines around return, dedent safe try/except/else clauses, then report what remains; exit 1 when unfixable violations remain.",
)
@click.option(
    "--only-autofixable",
    "only_autofixable",
    is_flag=True,
    help="Best effort: apply every available fix, report the rest, and exit 0 even when unfixable violations remain.",
)
@click.option(
    "--include",
    "include_entries",
    multiple=True,
    help="Rule code, group prefix, or __ALL__; repeatable. Overrides the config file's include list.",
)
@click.option(
    "--exclude",
    "exclude_entries",
    multiple=True,
    help="Rule code, group prefix, or __ALL__; repeatable. Overrides the config file's exclude list.",
)
@click.argument(
    "paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path)
)
def format_files(
    paths: tuple[Path, ...],
    only_autofixable: bool,
    include_entries: tuple[str, ...],
    exclude_entries: tuple[str, ...],
) -> None:
    enabled = _selection(include_entries, exclude_entries)
    if _report_files(paths, apply_fixes=True, enabled=enabled) and not only_autofixable:
        raise SystemExit(1)


def _selection(
    include_entries: tuple[str, ...],
    exclude_entries: tuple[str, ...],
) -> frozenset[RuleCode]:
    try:
        loaded = load_selection(Path.cwd(), include_entries, exclude_entries)
    except SelectionError as error:
        raise click.UsageError(str(error)) from error

    _declare(loaded)

    return loaded.enabled


def _declare(loaded: LoadedSelection) -> None:
    description = describe_selection(loaded.enabled)
    if loaded.config_file_found:
        click.echo(f"Found {CONFIG_FILE_NAME}. Running with: {description}", err=True)

        return

    if description == ALL_GROUP:
        click.echo(
            f"No {CONFIG_FILE_NAME} found, running with default '{ALL_GROUP}'", err=True
        )

        return

    click.echo(f"No {CONFIG_FILE_NAME} found, running with: {description}", err=True)


def _report_files(
    paths: tuple[Path, ...],
    apply_fixes: bool,
    enabled: frozenset[RuleCode],
) -> int:
    return sum(
        _process_file(file, apply_fixes, enabled) for file in python_files(paths)
    )


def _process_file(
    file: Path,
    apply_fixes: bool,
    enabled: frozenset[RuleCode],
) -> int:
    source = file.read_text(encoding="utf-8")
    checked = _formatted(file, source, enabled) if apply_fixes else source
    if checked != source:
        file.write_text(checked, encoding="utf-8")
        click.secho(f"fixed: {file}", fg="green")

    violations = find_violations(checked, enabled)
    for violation in violations:
        click.echo(
            f"{file}:{violation.line} {violation.rule.code} [{violation.rule.name}] {violation.message}"
        )

    return len(violations)


def _formatted(file: Path, source: str, enabled: frozenset[RuleCode]) -> str:
    try:
        return format_source(source, enabled)
    except RuntimeError as error:
        raise RuntimeError(f"{file}: {error}") from error
