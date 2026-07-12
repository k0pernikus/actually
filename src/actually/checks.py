from ast_grep_py import SgNode, SgRoot

from actually.spacing import ReturnSpacingGap, return_spacing_gaps
from actually.violations import Violation

ELSE_CONSTRUCT_BY_PARENT_KIND = {
    "for_statement": "for",
    "if_statement": "if",
    "try_statement": "try",
    "while_statement": "while",
}


def find_violations(source: str) -> tuple[Violation, ...]:
    root = SgRoot(source, "python").root()
    found = (
        *_else_violations(root),
        *_elif_violations(root),
        *_nested_ternary_violations(root),
        *_return_spacing_violations(source),
    )

    return tuple(sorted(found, key=lambda violation: violation.line))


def _else_violations(root: SgNode) -> tuple[Violation, ...]:
    return tuple(
        Violation(
            rule="no-else",
            line=_report_line(clause),
            message=f"banned `else` clause on `{ELSE_CONSTRUCT_BY_PARENT_KIND[_parent_of(clause).kind()]}` — restructure to guard clauses",
        )
        for clause in root.find_all(kind="else_clause")
    )


def _elif_violations(root: SgNode) -> tuple[Violation, ...]:
    return tuple(
        Violation(
            rule="no-elif",
            line=_report_line(clause),
            message="banned `elif` — use guard clauses or a dispatch table",
        )
        for clause in root.find_all(kind="elif_clause")
    )


def _nested_ternary_violations(root: SgNode) -> tuple[Violation, ...]:
    return tuple(
        Violation(
            rule="no-nested-ternary",
            line=_report_line(ternary),
            message="nested ternary — only flat conditional expressions are allowed",
        )
        for ternary in root.find_all(kind="conditional_expression")
        if _has_ternary_ancestor(ternary)
    )


def _return_spacing_violations(source: str) -> tuple[Violation, ...]:
    return tuple(_spacing_violation(gap) for gap in return_spacing_gaps(source))


def _spacing_violation(gap: ReturnSpacingGap) -> Violation:
    if gap.side == "above":
        return Violation(
            rule="blank-before-return",
            line=gap.return_start_line + 1,
            message="blank line required above `return` following other statements",
        )

    return Violation(
        rule="blank-after-return",
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


def _parent_of(node: SgNode) -> SgNode:
    parent = node.parent()
    if parent is None:
        raise ValueError(f"node of kind {node.kind()} has no parent")

    return parent


def _report_line(node: SgNode) -> int:
    return node.range().start.line + 1
