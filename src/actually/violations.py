from dataclasses import dataclass
from typing import Literal, get_args


RuleCode = Literal[
    "ACTI001",
    "ACTI002",
    "ACTI003",
    "ACTT001",
    "ACTT002",
    "ACTE001",
    "ACTE002",
    "ACTE003",
    "ACTH001",
    "ACTL001",
    "ACTL002",
    "ACTR001",
    "ACTR002",
]

RuleName = Literal[
    "no-if-else",
    "no-elif",
    "prefer-match",
    "ternary-not-nested",
    "ternary-not-empty",
    "no-try-else",
    "no-for-else",
    "no-while-else",
    "multi-line-chain",
    "trailing-comma",
    "one-element-per-line",
    "blank-before-return",
    "blank-after-return",
]

RuleGroup = Literal[
    "actually-chains",
    "actually-completion-clauses",
    "actually-if-conditions",
    "actually-literals",
    "actually-returns",
    "actually-ternaries",
]


@dataclass(frozen=True, slots=True)
class Rule:
    code: RuleCode
    name: RuleName
    group: RuleGroup


NO_IF_ELSE = Rule(code="ACTI001", name="no-if-else", group="actually-if-conditions")
NO_ELIF = Rule(code="ACTI002", name="no-elif", group="actually-if-conditions")
PREFER_MATCH = Rule(code="ACTI003", name="prefer-match", group="actually-if-conditions")
TERNARY_NOT_NESTED = Rule(code="ACTT001", name="ternary-not-nested", group="actually-ternaries")
TERNARY_NOT_EMPTY = Rule(code="ACTT002", name="ternary-not-empty", group="actually-ternaries")
NO_TRY_ELSE = Rule(code="ACTE001", name="no-try-else", group="actually-completion-clauses")
NO_FOR_ELSE = Rule(code="ACTE002", name="no-for-else", group="actually-completion-clauses")
NO_WHILE_ELSE = Rule(code="ACTE003", name="no-while-else", group="actually-completion-clauses")
MULTI_LINE_CHAIN = Rule(code="ACTH001", name="multi-line-chain", group="actually-chains")
TRAILING_COMMA = Rule(code="ACTL001", name="trailing-comma", group="actually-literals")
ONE_ELEMENT_PER_LINE = Rule(code="ACTL002", name="one-element-per-line", group="actually-literals")
BLANK_BEFORE_RETURN = Rule(code="ACTR001", name="blank-before-return", group="actually-returns")
BLANK_AFTER_RETURN = Rule(code="ACTR002", name="blank-after-return", group="actually-returns")

RULES: tuple[Rule, ...] = (
    NO_IF_ELSE,
    NO_ELIF,
    PREFER_MATCH,
    TERNARY_NOT_NESTED,
    TERNARY_NOT_EMPTY,
    NO_TRY_ELSE,
    NO_FOR_ELSE,
    NO_WHILE_ELSE,
    MULTI_LINE_CHAIN,
    TRAILING_COMMA,
    ONE_ELEMENT_PER_LINE,
    BLANK_BEFORE_RETURN,
    BLANK_AFTER_RETURN,
)


ALL_RULE_CODES: frozenset[RuleCode] = frozenset(rule.code for rule in RULES)

RuleGroupPrefix = Literal[
    "ACTE",
    "ACTH",
    "ACTI",
    "ACTL",
    "ACTR",
    "ACTT",
]

AllGroup = Literal["__ALL__"]

RuleSelector = AllGroup | RuleGroupPrefix | RuleCode

ALL_GROUP: AllGroup = "__ALL__"

RULE_GROUP_BY_PREFIX: dict[RuleGroupPrefix, RuleGroup] = {
    "ACTE": "actually-completion-clauses",
    "ACTH": "actually-chains",
    "ACTI": "actually-if-conditions",
    "ACTL": "actually-literals",
    "ACTR": "actually-returns",
    "ACTT": "actually-ternaries",
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
