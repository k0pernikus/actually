from ast_grep_py import SgNode, SgRoot


INDENT = "    "


def parsed_root(source: str) -> SgNode:
    return (SgRoot(source, "python")).root()


def inside_interpolation(node: SgNode) -> bool:
    ancestor = node.parent()
    while ancestor is not None:
        if ancestor.kind() == "interpolation":
            return True

        ancestor = ancestor.parent()

    return False


def outermost(nodes: list[SgNode]) -> tuple[SgNode, ...]:
    chosen: list[SgNode] = []
    for node in nodes:
        if not chosen or not _contains(chosen[-1], node):
            chosen.append(node)

    return tuple(chosen)


def start_position(node: SgNode) -> tuple[int, int]:
    return (
        (
            (node)  # well-actually: multi-line
            .range()
            .start.line
        ),
        (
            (node)  # well-actually: multi-line
            .range()
            .start.column
        ),
    )


def end_position(node: SgNode) -> tuple[int, int]:
    return (
        (
            (node)  # well-actually: multi-line
            .range()
            .end.line
        ),
        (
            (node)  # well-actually: multi-line
            .range()
            .end.column
        ),
    )


def leading_whitespace(text: str) -> str:
    return text[: len(text) - len(text.lstrip())]


def _contains(outer: SgNode, inner: SgNode) -> bool:
    return start_position(outer) <= start_position(inner) and end_position(inner) <= end_position(outer)
