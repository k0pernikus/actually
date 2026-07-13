import json

import pytest

from actually.reports import Finding, render_report
from actually.violations import NO_ELSE, TRAILING_COMMA, Violation

pytestmark = pytest.mark.unit

ELSE_FINDING = Finding(
    path="src/app.py",
    violation=Violation(
        rule=NO_ELSE,
        line=4,
        message="banned `else` clause on `if` — restructure to guard clauses",
    ),
)
COMMA_FINDING = Finding(
    path="src/data.py",
    violation=Violation(
        rule=TRAILING_COMMA,
        line=9,
        message="missing trailing comma after the last element",
    ),
)


def test_text_report_matches_the_terminal_line() -> None:
    report = render_report(
        "text",
        (ELSE_FINDING,),
        "9.9.9",
    )

    assert report == (
        "src/app.py:4 ACTC001 [no-else] banned `else` clause on `if` — restructure to guard clauses"
    )


def test_gitlab_report_is_code_climate_shaped() -> None:
    issues = json.loads(
        render_report(
            "gitlab",
            (
                ELSE_FINDING,
                COMMA_FINDING,
            ),
            "9.9.9",
        )
    )

    assert [issue["check_name"] for issue in issues] == [
        "ACTC001",
        "ACTL001",
    ]
    assert issues[0]["severity"] == "major"
    assert issues[0]["location"] == {
        "lines": {
            "begin": 4,
            "end": 4,
        },
        "path": "src/app.py",
    }
    fingerprints = {issue["fingerprint"] for issue in issues}
    assert len(fingerprints) == 2
    assert all(len(fingerprint) == 64 for fingerprint in fingerprints)


def test_gitlab_report_is_stable_across_renders() -> None:
    first = render_report("gitlab", (ELSE_FINDING,), "9.9.9")
    second = render_report("gitlab", (ELSE_FINDING,), "9.9.9")

    assert first == second


def test_empty_gitlab_report_is_an_empty_json_array() -> None:
    assert render_report("gitlab", (), "9.9.9") == "[]"


def test_github_report_is_a_workflow_command() -> None:
    report = render_report(
        "github",
        (ELSE_FINDING,),
        "9.9.9",
    )

    assert report == (
        "::error title=well-actually (ACTC001),file=src/app.py,line=4"
        "::banned `else` clause on `if` — restructure to guard clauses"
    )


def test_sarif_report_carries_tool_results_and_rule_help() -> None:
    document = json.loads(
        render_report(
            "sarif",
            (
                ELSE_FINDING,
                COMMA_FINDING,
            ),
            "9.9.9",
        )
    )

    assert document["version"] == "2.1.0"
    run = document["runs"][0]
    assert run["tool"]["driver"]["name"] == "well-actually"
    assert run["tool"]["driver"]["version"] == "9.9.9"
    assert [rule["id"] for rule in run["tool"]["driver"]["rules"]] == [
        "ACTC001",
        "ACTL001",
    ]
    assert run["tool"]["driver"]["rules"][0]["helpUri"] == (
        "https://github.com/k0pernikus/actually/blob/main/rules/no-else.md"
    )
    result = run["results"][0]
    assert result["ruleId"] == "ACTC001"
    assert result["level"] == "warning"
    assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 4
    assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == (
        "src/app.py"
    )
