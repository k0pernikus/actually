from ast_grep_py import SgNode, SgRoot

from actually.literals import LiteralLayoutGap, literal_layout_gaps
from actually.spacing import ReturnSpacingGap, return_spacing_gaps
from actually.violations import (
    BLANK_AFTER_RETURN,
    BLANK_BEFORE_RETURN,
    NO_ELIF,
    NO_ELSE,
    ONE_ELEMENT_PER_LINE,
    TERNARY_NOT_EMPTY,
    TERNARY_NOT_NESTED,
    TRAILING_COMMA,
    Violation,
)

ELSE_CONSTRUCT_BY_PARENT_KIND = {
    "for_statement": "for",
    "if_statement": "if",
    "try_statement": "try",
    "while_statement": "while",
}

EMPTY_CONTAINER_KINDS = frozenset(
    {
        "dictionary",
        "list",
        "tuple",
    },
)


def find_violations(source: str) -> tuple[Violation, ...]:
    root = SgRoot(source, "python").root()
    found = (
        *_else_violations(root),
        *_elif_violations(root),
        *_nested_ternary_violations(root),
        *_degenerate_ternary_violations(root),
        *_literal_layout_violations(source),
        *_return_spacing_violations(source),
    )

    return tuple(
        sorted(found, key=lambda violation: (violation.line, violation.rule.code))
    )


def _else_violations(root: SgNode) -> tuple[Violation, ...]:
    return tuple(
        Violation(
            rule=NO_ELSE,
            line=_report_line(clause),
            message=f"banned `else` clause on `{ELSE_CONSTRUCT_BY_PARENT_KIND[_parent_of(clause).kind()]}` — restructure to guard clauses",
        )
        for clause in root.find_all(kind="else_clause")
    )


def _elif_violations(root: SgNode) -> tuple[Violation, ...]:
    return tuple(
        Violation(
            rule=NO_ELIF,
            line=_report_line(clause),
            message="banned `elif` — use guard clauses or a dispatch table",
        )
        for clause in root.find_all(kind="elif_clause")
    )


def _nested_ternary_violations(root: SgNode) -> tuple[Violation, ...]:
    return tuple(
        Violation(
            rule=TERNARY_NOT_NESTED,
            line=_report_line(ternary),
            message="nested ternary — only flat conditional expressions are allowed",
        )
        for ternary in root.find_all(kind="conditional_expression")
        if _has_ternary_ancestor(ternary)
    )


def _degenerate_ternary_violations(root: SgNode) -> tuple[Violation, ...]:
    return tuple(
        Violation(
            rule=TERNARY_NOT_EMPTY,
            line=_report_line(ternary),
            message="degenerate ternary arm — a placeholder `None`/empty arm is a hidden `else`",
        )
        for ternary in root.find_all(kind="conditional_expression")
        if _has_degenerate_arm(ternary)
    )


def _literal_layout_violations(source: str) -> tuple[Violation, ...]:
    return tuple(_literal_violation(gap) for gap in literal_layout_gaps(source))


def _literal_violation(gap: LiteralLayoutGap) -> Violation:
    if gap.kind == "missing-trailing-comma":
        return Violation(
            rule=TRAILING_COMMA,
            line=gap.literal_start_line + 1,
            message="missing trailing comma after the last element",
        )

    return Violation(
        rule=ONE_ELEMENT_PER_LINE,
        line=gap.literal_start_line + 1,
        message="collection literal not one element per line with brackets on their own lines",
    )


def _return_spacing_violations(source: str) -> tuple[Violation, ...]:
    return tuple(_spacing_violation(gap) for gap in return_spacing_gaps(source))


def _spacing_violation(gap: ReturnSpacingGap) -> Violation:
    if gap.side == "above":
        return Violation(
            rule=BLANK_BEFORE_RETURN,
            line=gap.return_start_line + 1,
            message="blank line required above `return` following other statements",
        )

    return Violation(
        rule=BLANK_AFTER_RETURN,
        line=gap.return_start_line + 1,
        message="blank line required below `return` when code follows",
    )


def _has_ternary_ancestor(node: SgNode) -> bool:
    ancestor = node.parent()
    while ancestor is not None:
        if ancestor.kind() == "conditional_expression":
            return True

        ancestor = ancestor.parent()

    return False


def _has_degenerate_arm(ternary: SgNode) -> bool:
    consequence, alternative = _ternary_arms(ternary)

    return _is_degenerate_arm(consequence) or _is_degenerate_arm(alternative)


def _ternary_arms(ternary: SgNode) -> tuple[SgNode, SgNode]:
    operands = [
        child for child in ternary.children() if child.kind() not in ("if", "else")
    ]
    if len(operands) != 3:
        raise ValueError(
            f"expected three operands in a conditional_expression, found {len(operands)}"
        )

    return (operands[0], operands[2])


def _is_degenerate_arm(arm: SgNode) -> bool:
    if arm.kind() == "none":
        return True

    if arm.kind() == "string":
        return all(
            child.kind() in ("string_start", "string_end") for child in arm.children()
        )

    if arm.kind() in EMPTY_CONTAINER_KINDS:
        return not any(child.is_named() for child in arm.children())

    return False


def _parent_of(node: SgNode) -> SgNode:
    parent = node.parent()
    if parent is None:
        raise ValueError(f"node of kind {node.kind()} has no parent")

    return parent


def _report_line(node: SgNode) -> int:
    return node.range().start.line + 1
