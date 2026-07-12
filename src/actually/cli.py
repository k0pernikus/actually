from pathlib import Path

import rich_click as click

from actually.checks import find_violations
from actually.discovery import python_files
from actually.formatting import format_source


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
@click.argument(
    "paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path)
)
def check(paths: tuple[Path, ...]) -> None:
    if _report_files(paths, apply_fixes=False):
        raise SystemExit(1)


@main.command(
    name="format",
    help="Insert missing blank lines around return, dedent safe try/except/else clauses, then report what remains; exit 1 when unfixable violations remain.",
)
@click.argument(
    "paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path)
)
def format_files(paths: tuple[Path, ...]) -> None:
    if _report_files(paths, apply_fixes=True):
        raise SystemExit(1)


def _report_files(paths: tuple[Path, ...], apply_fixes: bool) -> int:
    return sum(_process_file(file, apply_fixes) for file in python_files(paths))


def _process_file(file: Path, apply_fixes: bool) -> int:
    source = file.read_text(encoding="utf-8")
    checked = _formatted(file, source) if apply_fixes else source
    if checked != source:
        file.write_text(checked, encoding="utf-8")
        click.secho(f"fixed: {file}", fg="green")

    violations = find_violations(checked)
    for violation in violations:
        click.echo(f"{file}:{violation.line} [{violation.rule}] {violation.message}")

    return len(violations)


def _formatted(file: Path, source: str) -> str:
    try:
        return format_source(source)
    except RuntimeError as error:
        raise RuntimeError(f"{file}: {error}") from error
