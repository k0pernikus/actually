from dataclasses import dataclass
from typing import Literal

from ast_grep_py import SgNode

from actually.sg_nodes import INDENT, end_position, inside_interpolation, leading_whitespace, parsed_root, start_position


ANCHOR_COMMENT = "# well-actually: multi-line"

SPINE_FIELD_BY_KIND = {
    "attribute": "object",
    "call": "function",
    "subscript": "value",
}

CALLED_OR_SUBSCRIPTED = frozenset(
    {
        "call",
        "subscript",
    },
)

WRAP_PARENT_KINDS = frozenset(
    {
        "expression_statement",
        "return_statement",
    },
)

ChainGapKind = Literal["chain-not-canonical", "stale-anchor"]

RewriteMode = Literal["explode-call", "inline", "wrap"]


@dataclass(frozen=True, slots=True)
class ChainLayoutGap:
    kind: ChainGapKind
    line: int
    autofixable: bool


@dataclass(frozen=True, slots=True)
class _Chain:
    top: SgNode
    base_end: tuple[int, int]
    base_parenthesized: bool
    segment_ends: tuple[tuple[int, int], ...]
    call_count: int
    fluent_count: int
    has_method_call: bool

    @property
    def needs_base_parens(self) -> bool:
        return self.fluent_count < 2 and not self.base_parenthesized


@dataclass(frozen=True, slots=True)
class _RewritePlan:
    target: SgNode
    mode: RewriteMode


def chain_layout_gaps(source: str) -> tuple[ChainLayoutGap, ...]:
    lines = source.split("\n")
    root = parsed_root(source)
    chains = _governed_chains(root)
    governed_base_lines = {chain.base_end[0] for chain in chains}
    layout_gaps = [
        ChainLayoutGap(kind="chain-not-canonical", line=start_position(chain.top)[0], autofixable=_is_explodable(chain, lines))
        for chain in chains
        if not _is_canonical(chain, lines)
    ]
    anchor_gaps = [
        ChainLayoutGap(kind="stale-anchor", line=comment.range().start.line, autofixable=True)
        for comment in _anchor_comments(root)
        if comment.range().start.line not in governed_base_lines
    ]

    return tuple(
        sorted(
            [
                *layout_gaps,
                *anchor_gaps,
            ],
            key=lambda gap: (gap.line, gap.kind),
        )
    )


def canonicalizable_chains(source: str) -> tuple[SgNode, ...]:
    lines = source.split("\n")

    return tuple(chain.top for chain in _governed_chains(parsed_root(source)) if not _is_canonical(chain, lines) and _is_explodable(chain, lines))


def explode_chains(source: str, tops: tuple[SgNode, ...]) -> str:
    lines = source.split("\n")
    rewritten_spans: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for top in sorted(tops, key=start_position, reverse=True):
        plan = _rewrite_plan(top)
        span = (start_position(plan.target), end_position(plan.target))
        if any(_overlaps(span, existing) for existing in rewritten_spans):
            continue

        lines = _rewritten(lines, top, plan)
        rewritten_spans.append(span)

    return "\n".join(lines)


def stale_anchor_removals(source: str) -> frozenset[int]:
    lines = source.split("\n")
    root = parsed_root(source)
    canonical_base_lines = {chain.base_end[0] for chain in _governed_chains(root) if _is_canonical(chain, lines)}

    return frozenset(comment.range().start.line for comment in _anchor_comments(root) if comment.range().start.line not in canonical_base_lines)


def strip_anchors(source: str, removal_lines: frozenset[int]) -> str:
    stripped = [_without_anchor(line) if index in removal_lines else line for index, line in enumerate(source.split("\n"))]
    survivors = [line for index, line in enumerate(stripped) if line or index not in removal_lines]

    return "\n".join(survivors)


def _governed_chains(root: SgNode) -> tuple[_Chain, ...]:
    chains = [_chain_of(top) for top in _maximal_spine_tops(root) if not inside_interpolation(top)]

    return tuple(chain for chain in chains if chain.call_count >= 2 and chain.has_method_call)


def _maximal_spine_tops(root: SgNode) -> tuple[SgNode, ...]:
    tops = [node for kind in sorted(SPINE_FIELD_BY_KIND) for node in root.find_all(kind=kind) if _is_spine_top(node)]

    return tuple(sorted(tops, key=start_position))


def _is_spine_top(node: SgNode) -> bool:
    parent = node.parent()
    if parent is None:
        return True

    field_name = SPINE_FIELD_BY_KIND.get(parent.kind())
    if field_name is None:
        return True

    return not _same_range(parent.field(field_name), node)


def _same_range(candidate: SgNode | None, node: SgNode) -> bool:
    if candidate is None:
        return False

    return start_position(candidate) == start_position(node) and end_position(candidate) == end_position(node)


def _chain_of(top: SgNode) -> _Chain:
    path = _spine_path(top)
    base_node, step_nodes = _base_and_step_nodes(path)
    steps = tuple(reversed(step_nodes))
    base_end, segment_ends = _segment_ends(base_node, steps)
    calls = tuple(node for node in path if node.kind() == "call")
    base_parenthesized = base_node.kind() == "parenthesized_expression"
    base_calls = _parenthesized_call_count(base_node) if base_parenthesized else 0

    return _Chain(
        top=top,
        base_end=base_end,
        base_parenthesized=base_parenthesized,
        segment_ends=segment_ends,
        call_count=len(calls) + base_calls,
        fluent_count=_fluent_count(path),
        has_method_call=any(_is_method_call(call) for call in calls),
    )


def _fluent_count(path: tuple[SgNode, ...]) -> int:
    return len([node for node in path if node.kind() == "attribute" and _value_is_called(node)])


def _value_is_called(attribute: SgNode) -> bool:
    value = _spine_field_node(attribute)

    return value.kind() in CALLED_OR_SUBSCRIPTED


def _base_and_step_nodes(path: tuple[SgNode, ...]) -> tuple[SgNode, tuple[SgNode, ...]]:
    bottom = path[-1]
    if bottom.kind() == "call":
        return bottom, path[:-1]

    call_indices = [index for index, node in enumerate(path) if node.kind() == "call"]
    if not call_indices:
        return _spine_field_node(bottom), path

    receiver_attribute = path[call_indices[-1] + 1]

    return _spine_field_node(receiver_attribute), path[: call_indices[-1] + 2]


def _is_method_call(call: SgNode) -> bool:
    function = _spine_field_node(call)

    return function.kind() == "attribute"


def _parenthesized_call_count(parenthesized: SgNode) -> int:
    named = [child for child in parenthesized.children() if child.is_named() and child.kind() != "comment"]
    if not named:
        return 0

    count = 0
    current = named[0]
    while current.kind() in SPINE_FIELD_BY_KIND:
        if current.kind() == "call":
            count += 1

        current = _spine_field_node(current)

    return count


def _spine_path(top: SgNode) -> tuple[SgNode, ...]:
    path = [
        top,
    ]
    while True:
        below = _spine_field_node(path[-1])
        if below.kind() not in SPINE_FIELD_BY_KIND:
            return tuple(path)

        path.append(below)


def _spine_field_node(node: SgNode) -> SgNode:
    field_name = SPINE_FIELD_BY_KIND[node.kind()]
    child = node.field(field_name)
    if child is None:
        raise ValueError(f"{node.kind()} node without a {field_name} field")

    return child


def _segment_ends(
    base_node: SgNode,
    steps: tuple[SgNode, ...],
) -> tuple[tuple[int, int], tuple[tuple[int, int], ...]]:
    base_end = end_position(base_node)
    ends: list[tuple[int, int]] = []
    open_attribute_run = False
    for step in steps:
        end = end_position(step)
        if step.kind() == "attribute":
            if open_attribute_run:
                ends[-1] = end
                continue

            ends.append(end)
            open_attribute_run = True
            continue

        open_attribute_run = False
        if ends:
            ends[-1] = end
            continue

        base_end = end

    return base_end, tuple(ends)


def _anchor_comments(root: SgNode) -> tuple[SgNode, ...]:
    return tuple(comment for comment in root.find_all(kind="comment") if comment.text() == ANCHOR_COMMENT)


def _is_canonical(chain: _Chain, lines: list[str]) -> bool:
    if chain.needs_base_parens:
        return False

    top_line, top_column = start_position(chain.top)
    if lines[top_line][:top_column].strip():
        return False

    base_line, base_column = chain.base_end
    if lines[base_line][base_column:] != f"  {ANCHOR_COMMENT}":
        return False

    previous = (base_line, len(lines[base_line]))
    for segment_end in chain.segment_ends:
        segment_slice = _slice_between(lines, previous, segment_end)
        leading = leading_whitespace(segment_slice)
        if "\n" not in leading:
            return False

        previous = segment_end

    return True


def _is_explodable(chain: _Chain, lines: list[str]) -> bool:
    if chain.top.find_all(kind="comment"):
        return False

    if not _has_single_line_pieces(chain, lines):
        return False

    return _is_explodable_context(chain, lines)


def _is_explodable_context(chain: _Chain, lines: list[str]) -> bool:
    parent = chain.top.parent()
    if parent is None:
        return False

    if parent.kind() == "parenthesized_expression":
        return _is_statement_expression(parent)

    if parent.kind() == "argument_list":
        if _is_explodable_call_context(parent):
            return True

        return _starts_own_line(chain.top, lines)

    return _is_statement_expression(chain.top)


def _starts_own_line(node: SgNode, lines: list[str]) -> bool:
    start_line, start_column = start_position(node)

    return not lines[start_line][:start_column].strip()


def _is_statement_expression(node: SgNode) -> bool:
    parent = node.parent()
    if parent is None:
        return False

    if parent.kind() in WRAP_PARENT_KINDS:
        return True

    if parent.kind() != "assignment":
        return False

    return _same_range(parent.field("right"), node)


def _is_explodable_call_context(argument_list: SgNode) -> bool:
    call = argument_list.parent()
    if call is None or call.kind() != "call":
        return False

    if not _is_spine_top(call):
        return False

    call_start_line, _ = start_position(call)
    call_end_line, _ = end_position(call)
    if call_start_line != call_end_line:
        return False

    return _is_statement_expression(call)


def _has_single_line_pieces(chain: _Chain, lines: list[str]) -> bool:
    return all("\n" not in piece for piece in _piece_slices(chain, lines))


def _piece_slices(chain: _Chain, lines: list[str]) -> tuple[str, ...]:
    boundaries = (start_position(chain.top), chain.base_end, *chain.segment_ends)

    return tuple(_stripped_slice(lines, start, end) for start, end in zip(boundaries, boundaries[1:], strict=False))


def _stripped_slice(lines: list[str], start: tuple[int, int], end: tuple[int, int]) -> str:
    piece = _slice_between(lines, start, end)

    return piece.strip()


def _slice_between(lines: list[str], start: tuple[int, int], end: tuple[int, int]) -> str:
    start_line, start_column = start
    end_line, end_column = end
    if start_line == end_line:
        return lines[start_line][start_column:end_column]

    middle = lines[start_line + 1 : end_line]

    return "\n".join([
        lines[start_line][start_column:],
        *middle,
        lines[end_line][:end_column],
    ])


def _rewrite_plan(top: SgNode) -> _RewritePlan:
    parent = top.parent()
    if parent is None:
        raise ValueError("chain top without a parent cannot be rewritten")

    if parent.kind() == "parenthesized_expression":
        return _RewritePlan(target=parent, mode="wrap")

    if parent.kind() == "argument_list":
        if _is_explodable_call_context(parent):
            call = parent.parent()
            if call is None:
                raise ValueError("argument_list without an enclosing call")

            return _RewritePlan(target=call, mode="explode-call")

        return _RewritePlan(target=top, mode="inline")

    return _RewritePlan(target=top, mode="wrap")


def _overlaps(
    left: tuple[tuple[int, int], tuple[int, int]],
    right: tuple[tuple[int, int], tuple[int, int]],
) -> bool:
    left_start, left_end = left
    right_start, right_end = right

    return left_start <= right_end and right_start <= left_end


def _rewritten(lines: list[str], top: SgNode, plan: _RewritePlan) -> list[str]:
    match plan.mode:
        case "explode-call":
            return _call_rewrite(lines, plan.target)

        case "inline":
            return _inline_rewrite(lines, _chain_of(top))

        case "wrap":
            return _wrap_rewrite(lines, _chain_of(top), plan.target)


def _inline_rewrite(lines: list[str], chain: _Chain) -> list[str]:
    start_line, start_column = start_position(chain.top)
    end_line, end_column = end_position(chain.top)
    indent = lines[start_line][:start_column]
    suffix = lines[end_line][end_column:]
    base, *segments = _piece_slices(chain, lines)
    anchored_base = f"({base})" if chain.needs_base_parens else base
    body = [
        f"{indent}{anchored_base}  {ANCHOR_COMMENT}",
        *[f"{indent}{segment}" for segment in segments],
    ]

    return [
        *lines[:start_line],
        *body[:-1],
        f"{body[-1]}{suffix}",
        *lines[end_line + 1 :],
    ]


def _wrap_rewrite(lines: list[str], chain: _Chain, target: SgNode) -> list[str]:
    start_line, start_column = start_position(target)
    end_line, end_column = end_position(target)
    start_text = lines[start_line]
    prefix = start_text[:start_column]
    suffix = lines[end_line][end_column:]
    indent = leading_whitespace(start_text)
    body_indent = indent + INDENT
    base, *segments = _piece_slices(chain, lines)
    anchored_base = f"({base})" if chain.needs_base_parens else base

    return [
        *lines[:start_line],
        f"{prefix}(",
        f"{body_indent}{anchored_base}  {ANCHOR_COMMENT}",
        *[f"{body_indent}{segment}" for segment in segments],
        f"{indent}){suffix}",
        *lines[end_line + 1 :],
    ]


def _call_rewrite(lines: list[str], call: SgNode) -> list[str]:
    argument_list = call.field("arguments")
    if argument_list is None:
        raise ValueError("call without an arguments field")

    start_line, start_column = start_position(call)
    end_line, end_column = end_position(call)
    head = _slice_between(lines, (start_line, start_column), start_position(argument_list))
    prefix = lines[start_line][:start_column]
    suffix = lines[end_line][end_column:]
    indent = leading_whitespace(lines[start_line])
    body_indent = indent + INDENT
    arguments = [child for child in argument_list.children() if child.is_named()]
    argument_lines = [line for argument in arguments for line in _argument_lines(argument, lines, body_indent)]

    return [
        *lines[:start_line],
        f"{prefix}{head}(",
        *argument_lines,
        f"{indent}){suffix}",
        *lines[end_line + 1 :],
    ]


def _argument_lines(argument: SgNode, lines: list[str], body_indent: str) -> list[str]:
    if not _is_fluent_argument(argument, lines):
        return [
            f"{body_indent}{argument.text()},",
        ]

    chain = _chain_of(argument)
    base, *segments = _piece_slices(chain, lines)
    anchored_base = f"({base})" if chain.needs_base_parens else base

    return [
        f"{body_indent}{anchored_base}  {ANCHOR_COMMENT}",
        *[f"{body_indent}{segment}" for segment in segments[:-1]],
        f"{body_indent}{segments[-1]},",
    ]


def _is_fluent_argument(argument: SgNode, lines: list[str]) -> bool:
    if argument.kind() not in SPINE_FIELD_BY_KIND:
        return False

    chain = _chain_of(argument)
    if chain.call_count < 2 or not chain.has_method_call:
        return False

    return _has_single_line_pieces(chain, lines)


def _without_anchor(line: str) -> str:
    position = line.rfind(ANCHOR_COMMENT)
    if position < 0:
        raise ValueError(f"line {line!r} carries no anchor to strip")

    return line[:position].rstrip()
