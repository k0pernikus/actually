from ast_grep_py import SgNode, SgRoot

from actually.spacing import ReturnSpacingGap, return_spacing_gaps

TERMINATING_KINDS = frozenset(
    {
        "break_statement",
        "continue_statement",
        "raise_statement",
        "return_statement",
    },
)

MAX_PASSES = 100


def format_source(source: str) -> str:
    dedented = _fix_try_else_clauses(source)

    return _fix_return_spacing(dedented)


def _fix_try_else_clauses(source: str) -> str:
    current = source
    for _ in range(MAX_PASSES):
        clauses = _safely_removable_else_clauses(current)
        if not clauses:
            return current

        current = _dedent_else_clause(current, clauses[0])

    raise RuntimeError("try/else dedents did not converge")


def _fix_return_spacing(source: str) -> str:
    current = source
    for _ in range(MAX_PASSES):
        gaps = return_spacing_gaps(current)
        if not gaps:
            return current

        current = _insert_blank_lines(current, _insertion_indices(gaps))

    raise RuntimeError("return spacing fixes did not converge")


def _safely_removable_else_clauses(source: str) -> tuple[SgNode, ...]:
    root = SgRoot(source, "python").root()

    return tuple(
        clause
        for clause in root.find_all(kind="else_clause")
        if _is_safely_removable(clause)
    )


def _is_safely_removable(clause: SgNode) -> bool:
    parent = clause.parent()
    if parent is None:
        return False

    if parent.kind() != "try_statement":
        return False

    child_kinds = [child.kind() for child in parent.children()]
    if "finally_clause" in child_kinds:
        return False

    if "except_group_clause" in child_kinds:
        return False

    except_clauses = [
        child for child in parent.children() if child.kind() == "except_clause"
    ]
    if not except_clauses:
        return False

    if not _block_starts_below_keyword(clause):
        return False

    return all(
        _ends_in_terminating_statement(except_clause)
        for except_clause in except_clauses
    )


def _block_starts_below_keyword(clause: SgNode) -> bool:
    return _clause_block(clause).range().start.line > clause.range().start.line


def _ends_in_terminating_statement(except_clause: SgNode) -> bool:
    statements = _clause_block(except_clause).children()
    if not statements:
        return False

    return statements[-1].kind() in TERMINATING_KINDS


def _clause_block(clause: SgNode) -> SgNode:
    blocks = [child for child in clause.children() if child.kind() == "block"]
    if len(blocks) != 1:
        raise ValueError(
            f"expected exactly one block under {clause.kind()}, found {len(blocks)}"
        )

    return blocks[0]


def _dedent_else_clause(source: str, clause: SgNode) -> str:
    block = _clause_block(clause)
    keyword_line = clause.range().start.line
    body_end = block.range().end.line
    shift = block.range().start.column - clause.range().start.column
    lines = source.split("\n")
    dedented_body = [
        _dedent_line(line, shift)
        for line in lines[block.range().start.line : body_end + 1]
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
    return frozenset(
        gap.return_start_line if gap.side == "above" else gap.return_end_line + 1
        for gap in gaps
    )


def _insert_blank_lines(source: str, indices: frozenset[int]) -> str:
    lines = source.split("\n")

    return "\n".join(
        piece
        for index, line in enumerate(lines)
        for piece in _line_with_insertion(index, line, indices)
    )


def _line_with_insertion(
    index: int, line: str, indices: frozenset[int]
) -> tuple[str, ...]:
    if index in indices:
        return ("", line)

    return (line,)
