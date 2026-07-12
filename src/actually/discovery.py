from pathlib import Path

EXCLUDED_DIRECTORY_NAMES = frozenset(
    {
        ".eggs",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "node_modules",
        "site-packages",
        "venv",
    },
)


def python_files(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    collected = [candidate for path in paths for candidate in _candidates(path)]

    return tuple(dict.fromkeys(collected))


def _candidates(path: Path) -> tuple[Path, ...]:
    if path.is_dir():
        return tuple(
            candidate
            for candidate in sorted(path.rglob("*.py"))
            if not _under_excluded_directory(candidate, path)
        )

    if path.suffix == ".py":
        return (path,)

    return ()


def _under_excluded_directory(candidate: Path, root: Path) -> bool:
    return any(
        part in EXCLUDED_DIRECTORY_NAMES for part in candidate.relative_to(root).parts
    )
