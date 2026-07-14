from collections.abc import Callable
from importlib.metadata import version as distribution_version
from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.table import Table

from actually.checks import find_violations
from actually.config import (
    LoadedSelection,
    SelectionError,
    load_selection,
    selection_declaration,
)
from actually.discovery import python_files
from actually.formatting import format_source
from actually.help_text import check_help, format_help
from actually.metadata import (
    FIX_LABELS,
    RuleCatalog,
    RuleMetadata,
    load_rule_catalog,
    rule_docs_url,
)
from actually.reports import (
    OUTPUT_FORMAT_BY_VALUE,
    Finding,
    OutputFormat,
    render_report,
)
from actually.violations import RuleCode


STDOUT_SENTINEL_PATH = "-"

HelpComposer = Callable[
    [
        frozenset[RuleCode],
        RuleCatalog,
        str,
    ],
    str,
]

HELP_COMPOSER_BY_COMMAND: dict[str, HelpComposer] = {
    "check": check_help,
    "format": format_help,
}

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


def _show_selection_aware_help(ctx: click.Context, _param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    ctx.command.help = _selection_aware_help_body(ctx)
    click.echo(ctx.get_help())
    ctx.exit()


INCLUDE_OPTION = click.option(
    "--include",
    "include_entries",
    multiple=True,
    is_eager=True,
    help="Rule code, group prefix, or __ALL__; repeatable. Overrides the config file's include list.",
)
EXCLUDE_OPTION = click.option(
    "--exclude",
    "exclude_entries",
    multiple=True,
    is_eager=True,
    help="Rule code, group prefix, or __ALL__; repeatable. Overrides the config file's exclude list.",
)
OUTPUT_FORMAT_OPTION = click.option(
    "--output-format",
    "output_format_value",
    type=click.Choice(sorted(OUTPUT_FORMAT_BY_VALUE)),
    default="text",
    show_default=True,
    help="Report format: gitlab (Code Climate JSON for the codequality artifact), github (workflow-command annotations), sarif (SARIF 2.1.0), or text.",
)
OUTPUT_FILE_OPTION = click.option(
    "--output-file",
    "output_file",
    default=STDOUT_SENTINEL_PATH,
    show_default=True,
    help="Write the report to this file; - means stdout.",
)
HELP_OPTION = click.option(
    "--help",
    "-h",
    "show_help",
    is_flag=True,
    expose_value=False,
    callback=_show_selection_aware_help,
    help="Show this message and exit.",
)


def _lint_command_options[CommandFunction: Callable[..., None]](command: CommandFunction) -> CommandFunction:
    return INCLUDE_OPTION(EXCLUDE_OPTION(OUTPUT_FORMAT_OPTION(OUTPUT_FILE_OPTION(HELP_OPTION(command)))))


@main.command(
    name="check",
    short_help="Report violations without modifying files; exit 1 when any are found.",
)
@_lint_command_options
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
def check(
    paths: tuple[Path, ...],
    include_entries: tuple[str, ...],
    exclude_entries: tuple[str, ...],
    output_format_value: str,
    output_file: str,
) -> None:
    enabled = _selection(include_entries, exclude_entries)
    findings = _collect_findings(paths, apply_fixes=False, enabled=enabled)
    _emit_report(_output_format(output_format_value), findings, output_file)
    if findings:
        raise SystemExit(1)


@main.command(
    name="format",
    short_help="Rewrite files with every auto-fix the active selection enables, then report what remains.",
)
@click.option(
    "--only-autofixable",
    "only_autofixable",
    is_flag=True,
    help="Best effort: apply every available fix, report the rest, and exit 0 even when unfixable violations remain.",
)
@_lint_command_options
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
def format_files(
    paths: tuple[Path, ...],
    only_autofixable: bool,
    include_entries: tuple[str, ...],
    exclude_entries: tuple[str, ...],
    output_format_value: str,
    output_file: str,
) -> None:
    enabled = _selection(include_entries, exclude_entries)
    findings = _collect_findings(paths, apply_fixes=True, enabled=enabled)
    _emit_report(_output_format(output_format_value), findings, output_file)
    if findings and not only_autofixable:
        raise SystemExit(1)


def _selection(
    include_entries: tuple[str, ...],
    exclude_entries: tuple[str, ...],
) -> frozenset[RuleCode]:
    loaded = _loaded_selection(include_entries, exclude_entries)
    _declare(loaded)

    return loaded.enabled


def _loaded_selection(
    include_entries: tuple[str, ...],
    exclude_entries: tuple[str, ...],
) -> LoadedSelection:
    try:
        return load_selection(Path.cwd(), include_entries, exclude_entries)
    except SelectionError as error:
        raise click.UsageError(str(error)) from error


def _declare(loaded: LoadedSelection) -> None:
    click.echo(selection_declaration(loaded.enabled, config_file_found=loaded.config_file_found), err=True)


def _selection_aware_help_body(ctx: click.Context) -> str:
    composer = _help_composer(ctx.command.name)
    loaded = _loaded_selection(
        _cli_entries(ctx.params, "include_entries"),
        _cli_entries(ctx.params, "exclude_entries"),
    )
    declaration = selection_declaration(loaded.enabled, config_file_found=loaded.config_file_found)

    return composer(loaded.enabled, load_rule_catalog(), declaration)


def _help_composer(command_name: str | None) -> HelpComposer:
    if command_name is None:
        raise ValueError("selection-aware help requires a named command")

    composer = HELP_COMPOSER_BY_COMMAND.get(command_name)
    if composer is None:
        raise ValueError(f"no selection-aware help composer registered for command {command_name!r}")

    return composer


def _cli_entries(params: dict[str, object], key: str) -> tuple[str, ...]:
    value = params.get(key)
    if not isinstance(value, tuple):
        raise TypeError(f"{key} must be parsed eagerly before help renders, got {value!r}")

    return tuple(_cli_entry(item, key) for item in value)


def _cli_entry(item: object, key: str) -> str:
    if not isinstance(item, str):
        raise TypeError(f"{key} entries must be strings, got {item!r}")

    return item


def _output_format(value: str) -> OutputFormat:
    return OUTPUT_FORMAT_BY_VALUE[value]


def _collect_findings(
    paths: tuple[Path, ...],
    apply_fixes: bool,
    enabled: frozenset[RuleCode],
) -> tuple[Finding, ...]:
    return tuple(finding for file in python_files(paths) for finding in _process_file(file, apply_fixes, enabled))


def _process_file(
    file: Path,
    apply_fixes: bool,
    enabled: frozenset[RuleCode],
) -> tuple[Finding, ...]:
    source = file.read_text(encoding="utf-8")
    checked = _formatted(file, source, enabled) if apply_fixes else source
    if checked != source:
        file.write_text(checked, encoding="utf-8")
        click.secho(f"fixed: {file}", fg="green", err=True)

    return tuple(Finding(path=str(file), violation=violation) for violation in find_violations(checked, enabled))


def _emit_report(
    output_format: OutputFormat,
    findings: tuple[Finding, ...],
    output_file: str,
) -> None:
    report = render_report(output_format, findings, distribution_version("well-actually"))
    if output_file != STDOUT_SENTINEL_PATH:
        (
            (Path(output_file))  # well-actually: multi-line
            .write_text(f"{report}\n", encoding="utf-8")
        )

        return

    if report:
        click.echo(report)


def _formatted(file: Path, source: str, enabled: frozenset[RuleCode]) -> str:
    try:
        return format_source(source, enabled)
    except RuntimeError as error:
        raise RuntimeError(f"{file}: {error}") from error
