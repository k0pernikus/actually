import re
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import rich_click as click


CZ_NO_COMMITS_FOUND = 3
CZ_NO_INCREMENT = 21
NOTHING_TO_RELEASE = frozenset({
    CZ_NO_COMMITS_FOUND,
    CZ_NO_INCREMENT,
})

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")

REPO_ROOT = (
    Path(__file__)  # well-actually: multi-line
    .resolve()
    .parent.parent
)


def _fail(message: str) -> NoReturn:
    raise click.ClickException(message)


def _run(argv: list[str]) -> None:
    completed = subprocess.run(argv, cwd=REPO_ROOT)
    if completed.returncode != 0:
        _fail(f"{' '.join(argv)} failed (exit {completed.returncode})")


def _capture(argv: list[str]) -> str:
    completed = subprocess.run(argv, cwd=REPO_ROOT, text=True, capture_output=True)
    if completed.returncode != 0:
        _fail(f"{' '.join(argv)} failed:\n{ANSI_ESCAPE.sub('', completed.stderr).strip()}")

    return (
        (ANSI_ESCAPE)  # well-actually: multi-line
        .sub("", completed.stdout)
        .strip()
    )


def _assert_on_main() -> None:
    branch = _capture([
        "git",
        "rev-parse",
        "--abbrev-ref",
        "HEAD",
    ])
    if branch != "main":
        _fail(f"releases are cut from main only, current branch is {branch!r}")


def _assert_clean_tree() -> None:
    status = _capture([
        "git",
        "status",
        "--porcelain",
    ])
    if status:
        _fail("working tree is dirty, commit or stash before releasing:\n" + status)


def _assert_in_sync() -> None:
    _run([
        "git",
        "fetch",
        "origin",
        "main",
    ])
    behind = _capture([
        "git",
        "rev-list",
        "--count",
        "main..origin/main",
    ])
    if behind != "0":
        _fail(f"main is {behind} commit(s) behind origin/main, pull before releasing")


def _current_version() -> str:
    return _capture([
        "uv",
        "version",
        "--short",
    ])


def _bump_argv(*, dry_run: bool) -> list[str]:
    base = [
        "uv",
        "run",
        "cz",
        "bump",
        "--yes",
        "--version-files-only",
    ]
    if dry_run:
        return [
            *base,
            "--dry-run",
        ]

    return base


def _bump(*, dry_run: bool) -> None:
    completed = subprocess.run(_bump_argv(dry_run=dry_run), cwd=REPO_ROOT)
    if completed.returncode == 0:
        return

    if completed.returncode in NOTHING_TO_RELEASE:
        _fail("nothing to release: no version increment from the commits since the last tag")

    _fail(f"cz bump failed (exit {completed.returncode})")


def _perform() -> None:
    previous = _current_version()
    _bump(dry_run=False)
    _run([
        "uv",
        "lock",
    ])
    current = _current_version()
    _run([
        "git",
        "add",
        "--",
        "pyproject.toml",
        "uv.lock",
    ])
    _run([
        "git",
        "commit",
        "--message",
        f"bump: version {previous} → {current}",
    ])
    tag = f"v{current}"
    _run([
        "git",
        "tag",
        "--annotate",
        tag,
        "--message",
        tag,
    ])
    _run([
        "git",
        "push",
        "--follow-tags",
    ])


def _confirm_or_fail() -> None:
    if not sys.stdin.isatty():
        _fail("non-interactive; pass --assume-yes to cut the release headlessly, or --dry-run to preview")

    _bump(dry_run=True)
    if not click.confirm("cut this release now — commit, tag, and push --follow-tags?", default=False):
        _fail("declined at the confirmation prompt")


@click.command()
@click.option("--dry-run", is_flag=True, help="preview the bump and make no changes")
@click.option("--assume-yes", "-y", is_flag=True, help="cut the release without the confirmation prompt")
def main(dry_run: bool, assume_yes: bool) -> None:
    _assert_on_main()
    _assert_clean_tree()
    _assert_in_sync()

    if dry_run:
        _bump(dry_run=True)

        return

    if not assume_yes:
        _confirm_or_fail()

    _perform()


if __name__ == "__main__":
    main()
