import re
from collections import Counter
from dataclasses import dataclass

from actually.sg_nodes import parsed_root
from actually.violations import NO_BANNED_SUPPRESSION, Violation


ALL_RULES = "*"
BARE_LABEL = "bare `# noqa` (no code named)"

_RULE_CODE = r"[A-Za-z]+\d+"
_CODE_LIST = rf"{_RULE_CODE}(?:\s*,\s*{_RULE_CODE})*"
_NOQA = re.compile(rf"#\s*(?:ruff\s*:\s*)?noqa(?:\s*:\s*(?P<codes>{_CODE_LIST}))?", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class Suppression:
    line: int
    codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SuppressionCount:
    code: str
    times: int

    @property
    def label(self) -> str:
        if self.code == ALL_RULES:
            return BARE_LABEL

        return f"Rule {self.code}"


def _codes_of(named: str | None) -> tuple[str, ...]:
    if named is None:
        return (ALL_RULES,)

    return tuple(
        (
            (code)  # well-actually: multi-line
            .strip()
            .upper()
        )
        for code in named.split(",")
        if code.strip()
    )


def suppressions(source: str) -> tuple[Suppression, ...]:
    found = []
    for comment in (parsed_root(source)).find_all(kind="comment"):
        match = _NOQA.search(comment.text())
        if match is None:
            continue

        line = (
            (comment)  # well-actually: multi-line
            .range()
            .start.line
        )
        found.append(Suppression(line=line + 1, codes=_codes_of(match["codes"])))

    return tuple(found)


def _is_banned(code: str, wanted: frozenset[str]) -> bool:
    if code == ALL_RULES:
        return True

    return code in wanted


def _message(code: str) -> str:
    if code == ALL_RULES:
        return "bare `# noqa` suppresses every rule, including the ones this project bans suppressing — name the code, or remove the directive and fix the finding"

    return f"`# noqa: {code}` suppresses a rule this project bans suppressing — a suppression records an unmet rule, it never grants an exception; remove it and fix the finding"


def banned_violations(source: str, banned: tuple[str, ...]) -> tuple[Violation, ...]:
    if not banned:
        return ()

    wanted = frozenset(code.upper() for code in banned)

    return tuple(
        Violation(
            rule=NO_BANNED_SUPPRESSION,
            line=found.line,
            message=_message(code),
            autofixable=False,
        )
        for found in suppressions(source)
        for code in found.codes
        if _is_banned(code, wanted)
    )


def counted(sources: tuple[str, ...], silenced: tuple[str, ...]) -> tuple[SuppressionCount, ...]:
    quiet = frozenset(code.upper() for code in silenced)
    tally: Counter[str] = Counter()
    for source in sources:
        for found in suppressions(source):
            tally.update(code for code in found.codes if code not in quiet)

    return tuple(SuppressionCount(code=code, times=times) for code, times in sorted(tally.items()))
