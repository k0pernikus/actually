from dataclasses import dataclass
from typing import Literal

from ast_grep_py import SgNode, SgRoot


LiteralGapKind = Literal["missing-trailing-comma", "elements-share-lines"]

LITERAL_BRACKETS = {
    "dictionary": ("{", "}"),
    "list": ("[", "]"),
    "set": ("{", "}"),
}

INDENT = "    "


@dataclass(frozen=True, slots=True)
class LiteralLayoutGap:
    kind: LiteralGapKind
    literal_start_line: int


@dataclass(frozen=True, slots=True)
class CommaInsertion:
    line: int
    column: int


def literal_layout_gaps(source: str) -> tuple[LiteralLayoutGap, ...]:
    gaps = [
        LiteralLayoutGap(kind=kind, literal_start_line=literal.range().start.line)
        for literal in _collection_literals(SgRoot(source, "python").root())
        for kind in _gap_kinds(literal)
    ]

    return tuple(sorted(gaps, key=lambda gap: (gap.literal_start_line, gap.kind)))


def canonicalizable_literals(source: str) -> tuple[SgNode, ...]:
    candidates = [literal for literal in _collection_literals(SgRoot(source, "python").root()) if not _is_one_element_per_line(literal) and _is_explodable(literal)]

    return _outermost(candidates)


def explode_collection_literals(source: str, literals: tuple[SgNode, ...]) -> str:
    lines = source.split("\n")
    for literal in sorted(literals, key=_start_position, reverse=True):
        lines = _exploded(lines, literal)

    return "\n".join(lines)


def missing_comma_insertions(source: str) -> tuple[CommaInsertion, ...]:
    return tuple(
        CommaInsertion(
            line=_elements(literal)[-1].range().end.line,
            column=_elements(literal)[-1].range().end.column,
        )
        for literal in _collection_literals(SgRoot(source, "python").root())
        if not _has_trailing_comma(literal)
    )


def insert_commas(source: str, insertions: tuple[CommaInsertion, ...]) -> str:
    lines = source.split("\n")
    for insertion in sorted(insertions, key=lambda entry: (entry.line, entry.column), reverse=True):
        text = lines[insertion.line]
        lines[insertion.line] = text[: insertion.column] + "," + text[insertion.column :]

    return "\n".join(lines)


def _gap_kinds(literal: SgNode) -> tuple[LiteralGapKind, ...]:
    kinds: list[LiteralGapKind] = []
    if not _has_trailing_comma(literal):
        kinds.append("missing-trailing-comma")

    if not _is_one_element_per_line(literal):
        kinds.append("elements-share-lines")

    return tuple(kinds)


def _collection_literals(root: SgNode) -> tuple[SgNode, ...]:
    literals = [node for kind in LITERAL_BRACKETS for node in root.find_all(kind=kind) if _elements(node) and not _inside_interpolation(node)]

    return tuple(sorted(literals, key=_start_position))


def _elements(literal: SgNode) -> tuple[SgNode, ...]:
    return tuple(child for child in literal.children() if child.is_named() and child.kind() != "comment")


def _inside_interpolation(node: SgNode) -> bool:
    ancestor = node.parent()
    while ancestor is not None:
        if ancestor.kind() == "interpolation":
            return True

        ancestor = ancestor.parent()

    return False


def _has_trailing_comma(literal: SgNode) -> bool:
    children = literal.children()
    last_element_index = max(index for index, child in enumerate(children) if child.is_named() and child.kind() != "comment")

    return any(child.kind() == "," for child in children[last_element_index + 1 :])


def _is_one_element_per_line(literal: SgNode) -> bool:
    elements = _elements(literal)
    if elements[0].range().start.line == literal.range().start.line:
        return False

    if elements[-1].range().end.line == literal.range().end.line:
        return False

    return all(later.range().start.line > earlier.range().end.line for earlier, later in zip(elements, elements[1:], strict=False))


def _is_explodable(literal: SgNode) -> bool:
    if any(child.kind() == "comment" for child in literal.children()):
        return False

    return all(element.range().start.line == element.range().end.line for element in _elements(literal))


def _outermost(literals: list[SgNode]) -> tuple[SgNode, ...]:
    chosen: list[SgNode] = []
    for literal in literals:
        if not chosen or not _contains(chosen[-1], literal):
            chosen.append(literal)

    return tuple(chosen)


def _contains(outer: SgNode, inner: SgNode) -> bool:
    return _start_position(outer) <= _start_position(inner) and (
        inner.range().end.line,
        inner.range().end.column,
    ) <= (outer.range().end.line, outer.range().end.column)


def _start_position(node: SgNode) -> tuple[int, int]:
    return (node.range().start.line, node.range().start.column)


def _exploded(lines: list[str], literal: SgNode) -> list[str]:
    open_bracket, close_bracket = LITERAL_BRACKETS[literal.kind()]
    start = literal.range().start
    end = literal.range().end
    start_line_text = lines[start.line]
    prefix = start_line_text[: start.column]
    suffix = lines[end.line][end.column :]
    indent = start_line_text[: len(start_line_text) - len(start_line_text.lstrip())]
    element_lines = [f"{indent}{INDENT}{element.text()}," for element in _elements(literal)]

    return [
        *lines[: start.line],
        prefix + open_bracket,
        *element_lines,
        f"{indent}{close_bracket}{suffix}",
        *lines[end.line + 1 :],
    ]
