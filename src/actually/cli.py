from pathlib import Path

import rich_click as click

from actually.checks import find_violations
from actually.config import SelectionError, load_selection
from actually.discovery import python_files
from actually.formatting import format_source
from actually.violations import RuleCode


@click.group(
    help="Well, actually — an opinionated Python linter: no else, no elif, flat ternaries only, breathing room around return."
)
@click.version_option(package_name="well-actually")
def main() -> None:
    pass


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
        return load_selection(Path.cwd(), include_entries, exclude_entries)
    except SelectionError as error:
        raise click.UsageError(str(error)) from error


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
