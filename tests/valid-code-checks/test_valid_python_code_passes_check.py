from pathlib import Path

import pytest

from actually.checks import find_violations
from actually.config import resolve_selection
from actually.formatting import format_source


pytestmark = pytest.mark.unit

RESOLVED_TEST_FILE = (
    (Path(__file__))  # well-actually: multi-line
    .resolve()
)

CASES_DIR = RESOLVED_TEST_FILE.parent / "allowed"

SELECTOR_CASES = tuple(
    (selector_dir.name, case_path) for selector_dir in sorted(path for path in CASES_DIR.iterdir() if path.is_dir()) for case_path in sorted(selector_dir.glob("*.py"))
)


def _case_id(case: tuple[str, Path]) -> str:
    selector, case_path = case

    return f"{selector}-{case_path.stem}"


@pytest.mark.parametrize("case", SELECTOR_CASES, ids=_case_id)
def test_valid_case_reports_no_violations_under_its_selector(case: tuple[str, Path]) -> None:
    selector, case_path = case
    enabled = resolve_selection((selector,), ())

    assert find_violations(case_path.read_text(encoding="utf-8"), enabled) == ()


@pytest.mark.parametrize("case", SELECTOR_CASES, ids=_case_id)
def test_valid_case_is_not_reformatted_under_its_selector(case: tuple[str, Path]) -> None:
    selector, case_path = case
    enabled = resolve_selection((selector,), ())
    source = case_path.read_text(encoding="utf-8")

    assert format_source(source, enabled) == source
