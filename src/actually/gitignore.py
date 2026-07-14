from pathlib import Path

from pathspec import GitIgnoreSpec


def ignored_by_gitignore(root: Path, candidates: tuple[Path, ...]) -> frozenset[Path]:
    if not candidates:
        return frozenset()

    specs = _gitignore_specs(root)
    if not specs:
        return frozenset()

    return frozenset(candidate for candidate in candidates if _is_ignored(candidate.resolve(), specs))


def _gitignore_specs(root: Path) -> tuple[tuple[Path, GitIgnoreSpec], ...]:
    resolved = root.resolve()
    carriers = [
        directory
        for directory in (
            *_ancestors_within_repo(resolved),
            *_descendant_carriers(resolved),
        )
        if (directory / ".gitignore").is_file()
    ]

    return tuple((directory, _spec_of(directory)) for directory in carriers)


def _ancestors_within_repo(root: Path) -> tuple[Path, ...]:
    walked: list[Path] = []
    current = root
    while True:
        walked.append(current)
        if (current / ".git").exists():
            return tuple(walked)

        if current.parent == current:
            return (root,)

        current = current.parent


def _descendant_carriers(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path.parent for path in root.rglob(".gitignore") if path.parent != root))


def _spec_of(directory: Path) -> GitIgnoreSpec:
    lines = (
        (directory / ".gitignore")  # well-actually: multi-line
        .read_text(encoding="utf-8")
        .splitlines()
    )

    return GitIgnoreSpec.from_lines(lines)


def _is_ignored(resolved_candidate: Path, specs: tuple[tuple[Path, GitIgnoreSpec], ...]) -> bool:
    applicable = [(directory, spec) for directory, spec in specs if directory in resolved_candidate.parents]
    deepest_first = sorted(applicable, key=lambda entry: len(entry[0].parts), reverse=True)
    for directory, spec in deepest_first:
        verdict = spec.check_file(
            (resolved_candidate)  # well-actually: multi-line
            .relative_to(directory)
            .as_posix(),
        )
        if verdict.include is not None:
            return verdict.include

    return False
