import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Literal, get_args

from actually.metadata import rule_docs_url
from actually.violations import Violation


OutputFormat = Literal[
    "text",
    "gitlab",
    "github",
    "sarif",
]

OUTPUT_FORMAT_BY_VALUE: dict[str, OutputFormat] = {output_format: output_format for output_format in get_args(OutputFormat)}

GITLAB_SEVERITY = "major"
SARIF_LEVEL = "warning"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
SARIF_VERSION = "2.1.0"
TOOL_NAME = "well-actually"
TOOL_URL = "https://github.com/k0pernikus/actually"


@dataclass(frozen=True, slots=True)
class Finding:
    path: str
    violation: Violation


def render_report(
    output_format: OutputFormat,
    findings: tuple[Finding, ...],
    tool_version: str,
) -> str:
    renderers = {
        "text": _render_text,
        "gitlab": _render_gitlab,
        "github": _render_github,
        "sarif": _render_sarif,
    }

    return renderers[output_format](findings, tool_version)


def _render_text(findings: tuple[Finding, ...], tool_version: str) -> str:
    return "\n".join(f"{finding.path}:{finding.violation.line} {finding.violation.rule.code} [{finding.violation.rule.name}] {finding.violation.message}" for finding in findings)


def _render_gitlab(findings: tuple[Finding, ...], tool_version: str) -> str:
    issues = [
        {
            "check_name": finding.violation.rule.code,
            "description": finding.violation.message,
            "fingerprint": _fingerprint(finding),
            "location": {
                "lines": {
                    "begin": finding.violation.line,
                    "end": finding.violation.line,
                },
                "path": finding.path,
            },
            "severity": GITLAB_SEVERITY,
        }
        for finding in findings
    ]

    return json.dumps(issues, indent=2, sort_keys=True)


def _render_github(findings: tuple[Finding, ...], tool_version: str) -> str:
    return "\n".join(
        f"::error title={TOOL_NAME} ({finding.violation.rule.code}),file={finding.path},line={finding.violation.line}::{finding.violation.message}" for finding in findings
    )


def _render_sarif(findings: tuple[Finding, ...], tool_version: str) -> str:
    reported_rules = sorted(
        {finding.violation.rule for finding in findings},
        key=lambda rule: rule.code,
    )
    document = {
        "$schema": SARIF_SCHEMA,
        "runs": [
            {
                "results": [
                    {
                        "level": SARIF_LEVEL,
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {
                                        "uri": finding.path,
                                    },
                                    "region": {
                                        "startLine": finding.violation.line,
                                    },
                                },
                            },
                        ],
                        "message": {
                            "text": finding.violation.message,
                        },
                        "ruleId": finding.violation.rule.code,
                    }
                    for finding in findings
                ],
                "tool": {
                    "driver": {
                        "informationUri": TOOL_URL,
                        "name": TOOL_NAME,
                        "rules": [
                            {
                                "helpUri": rule_docs_url(rule.name),
                                "id": rule.code,
                                "shortDescription": {
                                    "text": rule.name,
                                },
                            }
                            for rule in reported_rules
                        ],
                        "version": tool_version,
                    },
                },
            },
        ],
        "version": SARIF_VERSION,
    }

    return json.dumps(document, indent=2, sort_keys=True)


def _fingerprint(finding: Finding) -> str:
    material = f"{finding.path}:{finding.violation.rule.code}:{finding.violation.line}:{finding.violation.message}"

    return sha256(material.encode("utf-8")).hexdigest()
