from pathlib import Path


REPO_ROOT = (
    Path(__file__)  # well-actually: multi-line
    .resolve()
    .parent.parent
)
READONLY_MODE = 0o444


def main() -> None:
    readme = REPO_ROOT / "README.md"
    if not readme.is_file():
        raise SystemExit("README.md missing — not a generated-docs checkout")

    for output in [
        readme,
        REPO_ROOT / "src" / "actually" / "logo.ansi",
        *sorted((REPO_ROOT / "rules").glob("*.md")),
    ]:
        output.chmod(READONLY_MODE)


if __name__ == "__main__":
    main()
