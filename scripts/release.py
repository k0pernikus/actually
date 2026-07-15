import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import rich_click as click


REPO_ROOT = (
    Path(__file__)  # well-actually: multi-line
    .resolve()
    .parent.parent
)


def _run(argv: list[str]) -> None:
    subprocess.run(argv, cwd=REPO_ROOT, check=True)


def _capture(argv: list[str]) -> str:
    completed = subprocess.run(argv, cwd=REPO_ROOT, check=True, text=True, capture_output=True)

    return completed.stdout.strip()


def _abort(message: str) -> NoReturn:
    raise SystemExit(f"release aborted: {message}")


def _assert_on_main() -> None:
    branch = _capture([
        "git",
        "rev-parse",
        "--abbrev-ref",
        "HEAD",
    ])
    if branch != "main":
        _abort(f"releases are cut from main only, current branch is {branch!r}")


def _assert_clean_tree() -> None:
    status = _capture([
        "git",
        "status",
        "--porcelain",
    ])
    if status:
        _abort("working tree is dirty, commit or stash before releasing:\n" + status)


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
        _abort(f"main is {behind} commit(s) behind origin/main, pull before releasing")


def _current_version() -> str:
    return _capture([
        "uv",
        "version",
        "--short",
    ])


def _preview() -> None:
    _run([
        "uv",
        "run",
        "cz",
        "bump",
        "--dry-run",
        "--version-files-only",
        "--yes",
    ])


def _perform() -> None:
    previous = _current_version()
    _run([
        "uv",
        "run",
        "cz",
        "bump",
        "--yes",
        "--version-files-only",
    ])
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


def _require_consent(assume_yes: bool) -> None:
    if assume_yes:
        return

    if not sys.stdin.isatty():
        _abort("non-interactive; pass --assume-yes to cut the release headlessly, or --dry-run to preview")

    _preview()
    if not click.confirm("cut this release now — commit, tag, and push --follow-tags?", default=False):
        _abort("declined at the confirmation prompt")


@click.command()
@click.option("--dry-run", is_flag=True, help="preview the bump and make no changes")
@click.option("--assume-yes", "-y", is_flag=True, help="cut the release without the confirmation prompt")
def main(dry_run: bool, assume_yes: bool) -> None:
    _assert_on_main()
    _assert_clean_tree()
    _assert_in_sync()

    if dry_run:
        _preview()

        return

    _require_consent(assume_yes)
    _perform()


if __name__ == "__main__":
    main()
