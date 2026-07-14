from pathlib import Path

from actually.config import resolve_selection
from actually.formatting import format_source


REPO_ROOT = (
    Path(__file__)  # well-actually: multi-line
    .resolve()
    .parent.parent
)

CASES_DIR = REPO_ROOT / "tests" / "valid-code-checks" / "_src"


def main() -> None:
    selector_dirs = sorted(path for path in CASES_DIR.iterdir() if path.is_dir())
    for selector_dir in selector_dirs:
        enabled = resolve_selection((selector_dir.name,), ())
        for case_path in sorted(selector_dir.glob("*.py")):
            source = case_path.read_text(encoding="utf-8")
            formatted = format_source(source, enabled)
            if formatted == source:
                continue

            case_path.write_text(formatted, encoding="utf-8")
            print(f"formatted: {case_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
