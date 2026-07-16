from dataclasses import dataclass
from typing import Literal

from ast_grep_py import SgNode

from actually.sg_nodes import parsed_root


CLAUSE_KINDS = frozenset(
    {
        "case_clause",
        "elif_clause",
        "else_clause",
        "except_clause",
        "except_group_clause",
        "finally_clause",
    },
)

SCOPE_KINDS = frozenset(
    {
        "function_definition",
        "module",
    },
)


@dataclass(frozen=True, slots=True)
class ReturnSpacingGap:
    side: Literal["above", "below"]
    return_start_line: int
    return_end_line: int


def return_spacing_gaps(source: str) -> tuple[ReturnSpacingGap, ...]:
    root = parsed_root(source)

    return tuple(gap for statement in root.find_all(kind="return_statement") for gap in (*_gap_above(statement), *_gap_below(statement)))


def _gap_above(statement: SgNode) -> tuple[ReturnSpacingGap, ...]:
    preceding = _preceding_code_on_an_earlier_line(statement)
    if preceding is None:
        return ()

    if (
        (statement)  # well-actually: multi-line
        .range()
        .start.line
    ) - (
        (preceding)  # well-actually: multi-line
        .range()
        .end.line
    ) >= 2:
        return ()

    return (_gap(statement, "above"),)


def _gap_below(statement: SgNode) -> tuple[ReturnSpacingGap, ...]:
    following = _following_code(statement)
    if following is None:
        return ()

    if following.kind() in CLAUSE_KINDS:
        return ()

    if (
        (following)  # well-actually: multi-line
        .range()
        .start.line
    ) - (
        (statement)  # well-actually: multi-line
        .range()
        .end.line
    ) >= 2:
        return ()

    return (_gap(statement, "below"),)


def _gap(statement: SgNode, side: Literal["above", "below"]) -> ReturnSpacingGap:
    return ReturnSpacingGap(
        side=side,
        return_start_line=(
            (statement)  # well-actually: multi-line
            .range()
            .start.line
        ),
        return_end_line=(
            (statement)  # well-actually: multi-line
            .range()
            .end.line
        ),
    )


def _preceding_code_on_an_earlier_line(statement: SgNode) -> SgNode | None:
    current = statement.prev()
    while current is not None and (
        (current)  # well-actually: multi-line
        .range()
        .end.line
    ) == (
        (statement)  # well-actually: multi-line
        .range()
        .start.line
    ):
        current = current.prev()

    return current


def _following_code(statement: SgNode) -> SgNode | None:
    end_line = (
        (statement)  # well-actually: multi-line
        .range()
        .end.line
    )
    current = statement
    while True:
        sibling = current.next()
        if (
            sibling is not None
            and (
                (sibling)  # well-actually: multi-line
                .range()
                .start.line
            )
            == end_line
        ):
            current = sibling
            continue

        if sibling is not None:
            return sibling

        parent = current.parent()
        if parent is None:
            return None

        if parent.kind() in SCOPE_KINDS:
            return None

        current = parent
