from pathlib import Path

import pytest

from actually.checks import find_violations
from actually.formatting import format_source


pytestmark = pytest.mark.unit

VALID_CASES_DIR = Path(__file__).resolve().parent.parent / "python_sources" / "valid_cases"

VALID_CASE_PATHS = sorted(VALID_CASES_DIR.glob("*.py"))


def _case_id(path: Path) -> str:
    return path.stem


@pytest.mark.parametrize("case_path", VALID_CASE_PATHS, ids=_case_id)
def test_valid_case_reports_no_violations(case_path: Path) -> None:
    assert find_violations(case_path.read_text(encoding="utf-8")) == ()


@pytest.mark.parametrize("case_path", VALID_CASE_PATHS, ids=_case_id)
def test_valid_case_is_not_reformatted(case_path: Path) -> None:
    source = case_path.read_text(encoding="utf-8")

    assert format_source(source) == source
