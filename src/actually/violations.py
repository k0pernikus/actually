from dataclasses import dataclass
from typing import Literal, get_args


RuleCode = Literal[
    "ACTC001",
    "ACTC002",
    "ACTC003",
    "ACTC004",
    "ACTL001",
    "ACTL002",
    "ACTR001",
    "ACTR002",
]

RuleName = Literal[
    "no-else",
    "no-elif",
    "ternary-not-nested",
    "ternary-not-empty",
    "trailing-comma",
    "one-element-per-line",
    "blank-before-return",
    "blank-after-return",
]

RuleGroup = Literal[
    "actually-conditionals",
    "actually-literals",
    "actually-returns",
]


@dataclass(frozen=True, slots=True)
class Rule:
    code: RuleCode
    name: RuleName
    group: RuleGroup


NO_ELSE = Rule(code="ACTC001", name="no-else", group="actually-conditionals")
NO_ELIF = Rule(code="ACTC002", name="no-elif", group="actually-conditionals")
TERNARY_NOT_NESTED = Rule(code="ACTC003", name="ternary-not-nested", group="actually-conditionals")
TERNARY_NOT_EMPTY = Rule(code="ACTC004", name="ternary-not-empty", group="actually-conditionals")
TRAILING_COMMA = Rule(code="ACTL001", name="trailing-comma", group="actually-literals")
ONE_ELEMENT_PER_LINE = Rule(code="ACTL002", name="one-element-per-line", group="actually-literals")
BLANK_BEFORE_RETURN = Rule(code="ACTR001", name="blank-before-return", group="actually-returns")
BLANK_AFTER_RETURN = Rule(code="ACTR002", name="blank-after-return", group="actually-returns")

RULES: tuple[Rule, ...] = (
    NO_ELSE,
    NO_ELIF,
    TERNARY_NOT_NESTED,
    TERNARY_NOT_EMPTY,
    TRAILING_COMMA,
    ONE_ELEMENT_PER_LINE,
    BLANK_BEFORE_RETURN,
    BLANK_AFTER_RETURN,
)


ALL_RULE_CODES: frozenset[RuleCode] = frozenset(rule.code for rule in RULES)

RuleGroupPrefix = Literal[
    "ACTC",
    "ACTL",
    "ACTR",
]

AllGroup = Literal["__ALL__"]

RuleSelector = AllGroup | RuleGroupPrefix | RuleCode

ALL_GROUP: AllGroup = "__ALL__"

RULE_GROUP_BY_PREFIX: dict[RuleGroupPrefix, RuleGroup] = {
    "ACTC": "actually-conditionals",
    "ACTL": "actually-literals",
    "ACTR": "actually-returns",
}

RULE_SELECTOR_BY_VALUE: dict[str, RuleSelector] = {
    ALL_GROUP: ALL_GROUP,
    **{prefix: prefix for prefix in get_args(RuleGroupPrefix)},
    **{code: code for code in get_args(RuleCode)},
}


@dataclass(frozen=True, slots=True)
class Violation:
    rule: Rule
    line: int
    message: str
