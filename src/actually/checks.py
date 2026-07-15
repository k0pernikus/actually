from itertools import groupby

from ast_grep_py import SgNode

from actually.chains import ANCHOR_COMMENT, ChainLayoutGap, chain_layout_gaps
from actually.formatting import is_safely_removable
from actually.literals import LiteralLayoutGap, literal_layout_gaps
from actually.sg_nodes import parsed_root
from actually.spacing import ReturnSpacingGap, return_spacing_gaps
from actually.violations import (
    ALL_RULE_CODES,
    BLANK_AFTER_RETURN,
    BLANK_BEFORE_RETURN,
    MULTI_LINE_CHAIN,
    NO_ELIF,
    NO_FOR_ELSE,
    NO_IF_ELSE,
    NO_TRY_ELSE,
    NO_WHILE_ELSE,
    ONE_ELEMENT_PER_LINE,
    PREFER_MATCH,
    TERNARY_NOT_EMPTY,
    TERNARY_NOT_NESTED,
    TRAILING_COMMA,
    Rule,
    RuleCode,
    Violation,
)


ELSE_RULE_BY_PARENT_KIND: dict[str, Rule] = {
    "for_statement": NO_FOR_ELSE,
    "if_statement": NO_IF_ELSE,
    "try_statement": NO_TRY_ELSE,
    "while_statement": NO_WHILE_ELSE,
}

ELSE_MESSAGE_BY_PARENT_KIND = {
    "for_statement": "banned `else` on `for` — extract the search to a helper that returns early on a match",
    "if_statement": "banned `else` on `if` — restructure to guard clauses",
    "try_statement": "banned `else` on `try` — dedent the continuation after the `except` clauses",
    "while_statement": "banned `else` on `while` — restructure so the completion path is not an `else`",
}

EMPTY_CONTAINER_KINDS = frozenset(
    {
        "dictionary",
        "list",
        "tuple",
    },
)

TERNARY_KEYWORD_KINDS = frozenset(
    {
        "else",
        "if",
    },
)

STRING_DELIMITER_KINDS = frozenset(
    {
        "string_end",
        "string_start",
    },
)

BRANCH_CLAUSE_KINDS = frozenset(
    {
        "elif_clause",
        "else_clause",
    },
)


def find_violations(
    source: str,
    enabled: frozenset[RuleCode] = ALL_RULE_CODES,
) -> tuple[Violation, ...]:
    root = parsed_root(source)
    found = (
        *_else_violations(root),
        *_elif_violations(root),
        *_nested_ternary_violations(root),
        *_degenerate_ternary_violations(root),
        *_prefer_match_violations(root),
        *_chain_layout_violations(source),
        *_literal_layout_violations(source),
        *_return_spacing_violations(source),
    )

    return tuple(
        sorted(
            (violation for violation in found if violation.rule.code in enabled),
            key=lambda violation: (violation.line, violation.rule.code),
        )
    )


def _else_violations(root: SgNode) -> tuple[Violation, ...]:
    return tuple(_else_violation(clause) for clause in root.find_all(kind="else_clause"))


def _else_violation(clause: SgNode) -> Violation:
    parent = _parent_of(clause)
    parent_kind = parent.kind()

    return Violation(
        rule=ELSE_RULE_BY_PARENT_KIND[parent_kind],
        line=_report_line(clause),
        message=ELSE_MESSAGE_BY_PARENT_KIND[parent_kind],
        autofixable=is_safely_removable(clause),
    )


def _elif_violations(root: SgNode) -> tuple[Violation, ...]:
    return tuple(
        Violation(
            rule=NO_ELIF,
            line=_report_line(clause),
            message="banned `elif` — flatten to guard clauses with early exits",
            autofixable=False,
        )
        for clause in root.find_all(kind="elif_clause")
    )


def _nested_ternary_violations(root: SgNode) -> tuple[Violation, ...]:
    return tuple(
        Violation(
            rule=TERNARY_NOT_NESTED,
            line=_report_line(ternary),
            message="nested ternary — only flat conditional expressions are allowed",
            autofixable=False,
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
            autofixable=False,
        )
        for ternary in root.find_all(kind="conditional_expression")
        if _has_degenerate_arm(ternary)
    )


def _prefer_match_violations(root: SgNode) -> tuple[Violation, ...]:
    containers = (root, *root.find_all(kind="block"))

    return tuple(violation for container in containers for violation in _decision_table_violations(container))


def _decision_table_violations(container: SgNode) -> tuple[Violation, ...]:
    statements = tuple(child for child in container.children() if child.is_named())

    return tuple(
        Violation(
            rule=PREFER_MATCH,
            line=_report_line(run[0]),
            message="consecutive conditional returns dispatch on one subject — write one `match` statement",
            autofixable=False,
        )
        for run, follower in _conditional_return_runs(statements)
        if len(run) >= 2 and _is_decision_terminal(follower) and _dispatches_one_scrutinee(run)
    )


def _conditional_return_runs(statements: tuple[SgNode, ...]) -> tuple[tuple[tuple[SgNode, ...], SgNode], ...]:
    runs = []
    for is_conditional_return, group in groupby(enumerate(statements), key=_indexed_is_conditional_return):
        if not is_conditional_return:
            continue

        indexed = tuple(group)
        last_index, _ = indexed[-1]
        follower_index = last_index + 1
        if follower_index >= len(statements):
            continue

        runs.append((tuple(statement for _, statement in indexed), statements[follower_index]))

    return tuple(runs)


def _indexed_is_conditional_return(indexed: tuple[int, SgNode]) -> bool:
    _, statement = indexed

    return _is_conditional_return(statement)


def _is_conditional_return(statement: SgNode) -> bool:
    if statement.kind() != "if_statement":
        return False

    if any(child.kind() in BRANCH_CLAUSE_KINDS for child in statement.children()):
        return False

    body = _consequence_statements(statement)

    return len(body) == 1 and _is_value_return(body[0])


def _consequence_statements(statement: SgNode) -> tuple[SgNode, ...]:
    consequence = statement.field("consequence")
    if consequence is None:
        raise ValueError("if_statement without a consequence block")

    return tuple(child for child in consequence.children() if child.is_named())


def _is_value_return(statement: SgNode) -> bool:
    return statement.kind() == "return_statement" and any(child.is_named() for child in statement.children())


def _is_decision_terminal(statement: SgNode) -> bool:
    if statement.kind() == "raise_statement":
        return True

    return _is_value_return(statement)


def _dispatches_one_scrutinee(run: tuple[SgNode, ...]) -> bool:
    conditions = tuple(_condition_of(statement) for statement in run)

    return _shares_one_scrutinee(conditions)


def _condition_of(statement: SgNode) -> SgNode:
    condition = statement.field("condition")
    if condition is None:
        raise ValueError("if_statement without a condition")

    return condition


def _shares_one_scrutinee(conditions: tuple[SgNode, ...]) -> bool:
    if not all(condition.kind() == "comparison_operator" for condition in conditions):
        return False

    scrutinee_texts = {_first_operand_text(condition) for condition in conditions}

    return len(scrutinee_texts) == 1


def _first_operand_text(condition: SgNode) -> str:
    operands = tuple(child for child in condition.children() if child.is_named())
    if not operands:
        raise ValueError("comparison_operator without operands")

    first_operand = next(iter(operands))

    return first_operand.text()


def _chain_layout_violations(source: str) -> tuple[Violation, ...]:
    return tuple(_chain_violation(gap) for gap in chain_layout_gaps(source))


def _chain_violation(gap: ChainLayoutGap) -> Violation:
    if gap.kind == "stale-anchor":
        return Violation(
            rule=MULTI_LINE_CHAIN,
            line=gap.line + 1,
            message=f"stale `{ANCHOR_COMMENT}` anchor — no chain of two or more invocations starts here",
            autofixable=gap.autofixable,
        )

    return Violation(
        rule=MULTI_LINE_CHAIN,
        line=gap.line + 1,
        message=f"chain of two or more invocations — one call per line, base line anchored with `{ANCHOR_COMMENT}`",
        autofixable=gap.autofixable,
    )


def _literal_layout_violations(source: str) -> tuple[Violation, ...]:
    return tuple(_literal_violation(gap) for gap in literal_layout_gaps(source))


def _literal_violation(gap: LiteralLayoutGap) -> Violation:
    if gap.kind == "missing-trailing-comma":
        return Violation(
            rule=TRAILING_COMMA,
            line=gap.literal_start_line + 1,
            message="missing trailing comma after the last element",
            autofixable=gap.autofixable,
        )

    return Violation(
        rule=ONE_ELEMENT_PER_LINE,
        line=gap.literal_start_line + 1,
        message="collection literal not one element per line with brackets on their own lines",
        autofixable=gap.autofixable,
    )


def _return_spacing_violations(source: str) -> tuple[Violation, ...]:
    return tuple(_spacing_violation(gap) for gap in return_spacing_gaps(source))


def _spacing_violation(gap: ReturnSpacingGap) -> Violation:
    if gap.side == "above":
        return Violation(
            rule=BLANK_BEFORE_RETURN,
            line=gap.return_start_line + 1,
            message="blank line required above `return` following other statements",
            autofixable=True,
        )

    return Violation(
        rule=BLANK_AFTER_RETURN,
        line=gap.return_start_line + 1,
        message="blank line required below `return` when code follows",
        autofixable=True,
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
    operands = [child for child in ternary.children() if child.kind() not in TERNARY_KEYWORD_KINDS]
    if len(operands) != 3:
        raise ValueError(f"expected three operands in a conditional_expression, found {len(operands)}")

    return (operands[0], operands[2])


def _is_degenerate_arm(arm: SgNode) -> bool:
    match arm.kind():
        case "none":
            return True

        case "string":
            return all(child.kind() in STRING_DELIMITER_KINDS for child in arm.children())

        case kind if kind in EMPTY_CONTAINER_KINDS:
            return not any(child.is_named() for child in arm.children())

        case _:
            return False


def _parent_of(node: SgNode) -> SgNode:
    parent = node.parent()
    if parent is None:
        raise ValueError(f"node of kind {node.kind()} has no parent")

    return parent


def _report_line(node: SgNode) -> int:
    return node.range().start.line + 1
