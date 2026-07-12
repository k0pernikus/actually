from dataclasses import dataclass
from typing import Literal

RuleCode = Literal[
    "ACTC001",
    "ACTC002",
    "ACTC003",
    "ACTC004",
    "ACTR001",
    "ACTR002",
]

RuleName = Literal[
    "no-else",
    "no-elif",
    "ternary-not-nested",
    "ternary-not-empty",
    "blank-before-return",
    "blank-after-return",
]

RuleGroup = Literal[
    "actually-conditionals",
    "actually-returns",
]


@dataclass(frozen=True, slots=True)
class Rule:
    code: RuleCode
    name: RuleName
    group: RuleGroup


NO_ELSE = Rule(code="ACTC001", name="no-else", group="actually-conditionals")
NO_ELIF = Rule(code="ACTC002", name="no-elif", group="actually-conditionals")
TERNARY_NOT_NESTED = Rule(
    code="ACTC003", name="ternary-not-nested", group="actually-conditionals"
)
TERNARY_NOT_EMPTY = Rule(
    code="ACTC004", name="ternary-not-empty", group="actually-conditionals"
)
BLANK_BEFORE_RETURN = Rule(
    code="ACTR001", name="blank-before-return", group="actually-returns"
)
BLANK_AFTER_RETURN = Rule(
    code="ACTR002", name="blank-after-return", group="actually-returns"
)

RULES: tuple[Rule, ...] = (
    NO_ELSE,
    NO_ELIF,
    TERNARY_NOT_NESTED,
    TERNARY_NOT_EMPTY,
    BLANK_BEFORE_RETURN,
    BLANK_AFTER_RETURN,
)


@dataclass(frozen=True, slots=True)
class Violation:
    rule: Rule
    line: int
    message: str
