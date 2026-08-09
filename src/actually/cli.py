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
    SuppressionPolicy,
    load_selection,
    selection_declaration,
)
from actually.discovery import python_files
from actually.formatting import format_source
from actually.help_text import check_help, format_help
from actually.logo import render_logo
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
from actually.suppressions import banned_violations, counted
from actually.violations import NO_BANNED_SUPPRESSION, RuleCode


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


def _print_version(ctx: click.Context, _param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return

    click.echo(render_logo(), nl=False)
    click.echo(f"actually, version {distribution_version('well-actually')}")
    ctx.exit()


@click.group(
    help="Well, actually — an opinionated Python linter: no else, no elif, flat ternaries only, breathing room around return.",
    context_settings={
        "help_option_names": [
            "-h",
            "--help",
        ],
    },
)
@click.option(
    "-v",
    "--version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_print_version,
    help="Show the rainbow banner and version, then exit.",
)
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


def _format_command_options[CommandFunction: Callable[..., None]](command: CommandFunction) -> CommandFunction:
    return INCLUDE_OPTION(EXCLUDE_OPTION(HELP_OPTION(command)))


@main.command(
    name="check",
    short_help="Report violations without modifying files; exit 1 when any are found.",
)
@click.option(
    "--only-autofixable",
    "only_autofixable",
    is_flag=True,
    help="Report only the violations `format` mechanically fixes — the formatter gate.",
)
@click.option(
    "--ignore-autofixable",
    "ignore_autofixable",
    is_flag=True,
    help="Report only the violations a human must resolve — the code-quality set.",
)
@_lint_command_options
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
def check(
    paths: tuple[Path, ...],
    only_autofixable: bool,
    ignore_autofixable: bool,
    include_entries: tuple[str, ...],
    exclude_entries: tuple[str, ...],
    output_format_value: str,
    output_file: str,
) -> None:
    _reject_conflicting_filters(only_autofixable, ignore_autofixable)
    loaded = _loaded_selection(include_entries, exclude_entries)
    _declare(loaded)
    policy = _active_policy(loaded)
    findings = _autofixable_scoped(_collect_findings(paths, loaded.enabled, policy), only_autofixable, ignore_autofixable)
    _emit_report(_output_format(output_format_value), findings, output_file)
    _warn_suppressions(paths, policy)
    if findings:
        raise SystemExit(1)


@main.command(
    name="format",
    short_help="Apply every auto-fix the active selection enables; print only the files it changes.",
)
@_format_command_options
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
def format_files(
    paths: tuple[Path, ...],
    include_entries: tuple[str, ...],
    exclude_entries: tuple[str, ...],
) -> None:
    enabled = _loaded_selection(include_entries, exclude_entries).enabled
    _apply_fixes(paths, enabled)


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


def _reject_conflicting_filters(only_autofixable: bool, ignore_autofixable: bool) -> None:
    if only_autofixable and ignore_autofixable:
        raise click.UsageError("--only-autofixable and --ignore-autofixable are mutually exclusive")


def _autofixable_scoped(
    findings: tuple[Finding, ...],
    only_autofixable: bool,
    ignore_autofixable: bool,
) -> tuple[Finding, ...]:
    if only_autofixable:
        return tuple(finding for finding in findings if finding.violation.autofixable)

    if ignore_autofixable:
        return tuple(finding for finding in findings if not finding.violation.autofixable)

    return findings


def _active_policy(loaded: LoadedSelection) -> SuppressionPolicy:
    if NO_BANNED_SUPPRESSION.code in loaded.enabled:
        return loaded.suppressions

    return SuppressionPolicy(silenced=loaded.suppressions.silenced)


def _collect_findings(
    paths: tuple[Path, ...],
    enabled: frozenset[RuleCode],
    policy: SuppressionPolicy,
) -> tuple[Finding, ...]:
    return tuple(finding for file in python_files(paths) for finding in _file_findings(file, enabled, policy))


def _file_findings(
    file: Path,
    enabled: frozenset[RuleCode],
    policy: SuppressionPolicy,
) -> tuple[Finding, ...]:
    source = file.read_text(encoding="utf-8")
    violations = (
        *find_violations(source, enabled),
        *banned_violations(source, policy.banned),
    )

    return tuple(Finding(path=str(file), violation=violation) for violation in violations)


def _warn_suppressions(paths: tuple[Path, ...], policy: SuppressionPolicy) -> None:
    sources = tuple(file.read_text(encoding="utf-8") for file in python_files(paths))
    for count in counted(sources, policy.silenced):
        click.secho(f"WARN: {count.label} suppressed {count.times} times", fg="yellow", err=True)


def _apply_fixes(paths: tuple[Path, ...], enabled: frozenset[RuleCode]) -> None:
    for file in python_files(paths):
        source = file.read_text(encoding="utf-8")
        formatted = _formatted(file, source, enabled)
        if formatted == source:
            continue

        file.write_text(formatted, encoding="utf-8")
        click.secho(f"fixed: {file}", fg="green", err=True)


def _emit_report(
    output_format: OutputFormat,
    findings: tuple[Finding, ...],
    output_file: str,
) -> None:
    report = render_report(output_format, findings, distribution_version("well-actually"))
    if output_file != STDOUT_SENTINEL_PATH:
        ((Path(output_file)).write_text(f"{report}\n", encoding="utf-8"))

        return

    if report:
        click.echo(report)


def _formatted(file: Path, source: str, enabled: frozenset[RuleCode]) -> str:
    try:
        return format_source(source, enabled)
    except RuntimeError as error:
        raise RuntimeError(f"{file}: {error}") from error
