import json

import pytest

from actually.reports import Finding, OutputFormat, render_report
from actually.violations import NO_IF_ELSE, TRAILING_COMMA, Violation


pytestmark = pytest.mark.unit

ELSE_FINDING = Finding(
    path="src/app.py",
    violation=Violation(
        rule=NO_IF_ELSE,
        line=4,
        message="banned `else` on `if` — restructure to guard clauses",
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


@pytest.mark.parametrize(
    ("output_format", "findings", "expected"),
    [
        pytest.param(
            "text",
            (
                Finding(
                    path="src/app.py",
                    violation=Violation(
                        rule=NO_IF_ELSE,
                        line=4,
                        message="banned `else` on `if` — restructure to guard clauses",
                    ),
                ),
            ),
            "src/app.py:4 ACTI001 [no-if-else] banned `else` on `if` — restructure to guard clauses",
            id="text-terminal-line",
        ),
        pytest.param(
            "github",
            (
                Finding(
                    path="src/app.py",
                    violation=Violation(
                        rule=NO_IF_ELSE,
                        line=4,
                        message="banned `else` on `if` — restructure to guard clauses",
                    ),
                ),
            ),
            "::error title=well-actually (ACTI001),file=src/app.py,line=4::banned `else` on `if` — restructure to guard clauses",
            id="github-workflow-command",
        ),
        pytest.param(
            "gitlab",
            (),
            "[]",
            id="gitlab-empty-array",
        ),
    ],
)
def test_report_output_is_byte_exact(
    output_format: OutputFormat,
    findings: tuple[Finding, ...],
    expected: str,
) -> None:
    assert render_report(output_format, findings, "9.9.9") == expected


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
        "ACTI001",
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
        "ACTI001",
        "ACTL001",
    ]
    assert run["tool"]["driver"]["rules"][0]["helpUri"] == ("https://github.com/k0pernikus/actually/blob/main/rules/no-if-else.md")
    result = run["results"][0]
    assert result["ruleId"] == "ACTI001"
    assert result["level"] == "warning"
    assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 4
    assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == ("src/app.py")
