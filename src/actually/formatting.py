from ast_grep_py import SgNode

from actually.chains import (
    canonicalizable_chains,
    explode_chains,
    stale_anchor_removals,
    strip_anchors,
)
from actually.literals import (
    canonicalizable_literals,
    explode_collection_literals,
    insert_commas,
    missing_comma_insertions,
)
from actually.sg_nodes import parsed_root, start_position
from actually.spacing import ReturnSpacingGap, return_spacing_gaps
from actually.violations import (
    ALL_RULE_CODES,
    BLANK_AFTER_RETURN,
    BLANK_BEFORE_RETURN,
    MULTI_LINE_CHAIN,
    NO_TRY_ELSE,
    ONE_ELEMENT_PER_LINE,
    TRAILING_COMMA,
    RuleCode,
)


TERMINATING_KINDS = frozenset(
    {
        "break_statement",
        "continue_statement",
        "raise_statement",
        "return_statement",
    },
)

SPACING_RULE_CODE_BY_SIDE = {
    "above": BLANK_BEFORE_RETURN.code,
    "below": BLANK_AFTER_RETURN.code,
}

TRY_DEDENT_BLOCKER_KINDS = frozenset(
    {
        "except_group_clause",
        "finally_clause",
    },
)

MAX_PASSES = 100


def format_source(
    source: str,
    enabled: frozenset[RuleCode] = ALL_RULE_CODES,
) -> str:
    current = _fix_chain_layout(source, enabled)
    current = _fix_literal_layout(current, enabled)
    if NO_TRY_ELSE.code in enabled:
        current = _fix_try_else_clauses(current)

    return _fix_return_spacing(current, enabled)


def _fix_chain_layout(source: str, enabled: frozenset[RuleCode]) -> str:
    if MULTI_LINE_CHAIN.code not in enabled:
        return source

    current = source
    for _ in range(MAX_PASSES):
        removals = stale_anchor_removals(current)
        if removals:
            current = strip_anchors(current, removals)
            continue

        chains = canonicalizable_chains(current)
        if chains:
            current = explode_chains(current, chains)
            continue

        return current

    raise RuntimeError("chain layout fixes did not converge")


def _fix_literal_layout(source: str, enabled: frozenset[RuleCode]) -> str:
    current = source
    for _ in range(MAX_PASSES):
        if ONE_ELEMENT_PER_LINE.code in enabled:
            explodable = canonicalizable_literals(current)
            if explodable:
                current = explode_collection_literals(current, explodable)
                continue

        if TRAILING_COMMA.code in enabled:
            insertions = missing_comma_insertions(current)
            if insertions:
                current = insert_commas(current, insertions)
                continue

        return current

    raise RuntimeError("literal layout fixes did not converge")


def _fix_try_else_clauses(source: str) -> str:
    current = source
    for _ in range(MAX_PASSES):
        clauses = _safely_removable_else_clauses(current)
        if not clauses:
            return current

        current = _dedent_else_clause(current, clauses[0])

    raise RuntimeError("try/else dedents did not converge")


def _fix_return_spacing(source: str, enabled: frozenset[RuleCode]) -> str:
    current = source
    for _ in range(MAX_PASSES):
        gaps = tuple(gap for gap in return_spacing_gaps(current) if SPACING_RULE_CODE_BY_SIDE[gap.side] in enabled)
        if not gaps:
            return current

        current = _insert_blank_lines(current, _insertion_indices(gaps))

    raise RuntimeError("return spacing fixes did not converge")


def _safely_removable_else_clauses(source: str) -> tuple[SgNode, ...]:
    root = parsed_root(source)

    return tuple(clause for clause in root.find_all(kind="else_clause") if is_safely_removable(clause))


def is_safely_removable(clause: SgNode) -> bool:
    parent = clause.parent()
    if parent is None:
        return False

    if not _is_plain_try_statement(parent):
        return False

    if not _block_starts_below_keyword(clause):
        return False

    return _every_except_clause_exits(parent)


def _is_plain_try_statement(parent: SgNode) -> bool:
    if parent.kind() != "try_statement":
        return False

    child_kinds = {child.kind() for child in parent.children()}

    return not child_kinds & TRY_DEDENT_BLOCKER_KINDS


def _every_except_clause_exits(parent: SgNode) -> bool:
    except_clauses = [child for child in parent.children() if child.kind() == "except_clause"]
    if not except_clauses:
        return False

    return all(_ends_in_terminating_statement(except_clause) for except_clause in except_clauses)


def _block_starts_below_keyword(clause: SgNode) -> bool:
    block_line, _ = start_position(_clause_block(clause))
    keyword_line, _ = start_position(clause)

    return block_line > keyword_line


def _ends_in_terminating_statement(except_clause: SgNode) -> bool:
    statements = (_clause_block(except_clause)).children()
    if not statements:
        return False

    return statements[-1].kind() in TERMINATING_KINDS


def _clause_block(clause: SgNode) -> SgNode:
    blocks = [child for child in clause.children() if child.kind() == "block"]
    if len(blocks) != 1:
        raise ValueError(f"expected exactly one block under {clause.kind()}, found {len(blocks)}")

    return blocks[0]


def _dedent_else_clause(source: str, clause: SgNode) -> str:
    block = _clause_block(clause)
    keyword_line = (
        (clause)  # well-actually: multi-line
        .range()
        .start.line
    )
    body_end = (
        (block)  # well-actually: multi-line
        .range()
        .end.line
    )
    shift = (
        (block)  # well-actually: multi-line
        .range()
        .start.column
    ) - (
        (clause)  # well-actually: multi-line
        .range()
        .start.column
    )
    lines = source.split("\n")
    dedented_body = [
        _dedent_line(line, shift)
        for line in lines[
            (
                (block)  # well-actually: multi-line
                .range()
                .start.line
            ) : body_end + 1
        ]
    ]

    return "\n".join(
        [
            *lines[:keyword_line],
            *dedented_body,
            *lines[body_end + 1 :],
        ],
    )


def _dedent_line(line: str, shift: int) -> str:
    if not line.strip():
        return line

    if line[:shift].strip():
        return line

    return line[shift:]


def _insertion_indices(gaps: tuple[ReturnSpacingGap, ...]) -> frozenset[int]:
    return frozenset(gap.return_start_line if gap.side == "above" else gap.return_end_line + 1 for gap in gaps)


def _insert_blank_lines(source: str, indices: frozenset[int]) -> str:
    lines = source.split("\n")

    return "\n".join(piece for index, line in enumerate(lines) for piece in _line_with_insertion(index, line, indices))


def _line_with_insertion(index: int, line: str, indices: frozenset[int]) -> tuple[str, ...]:
    if index in indices:
        return ("", line)

    return (line,)
