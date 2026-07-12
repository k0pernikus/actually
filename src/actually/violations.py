from dataclasses import dataclass
from typing import Literal

RuleName = Literal[
    "no-else",
    "no-elif",
    "no-nested-ternary",
    "blank-before-return",
    "blank-after-return",
]


@dataclass(frozen=True, slots=True)
class Violation:
    rule: RuleName
    line: int
    message: str
