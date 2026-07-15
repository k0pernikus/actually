import pytest

from actually.checks import find_violations
from actually.formatting import format_source


pytestmark = pytest.mark.unit


def outline(source: str) -> list[tuple[str, int]]:
    return [(violation.rule.code, violation.line) for violation in find_violations(source)]


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "value = make(1).build()\n",
            [
                ("ACTH001", 1),
            ],
            id="two-call-single-line-flagged",
        ),
        pytest.param(
            "value = make(1).build().render()\n",
            [
                ("ACTH001", 1),
            ],
            id="three-call-single-line-flagged",
        ),
        pytest.param(
            "value = (\n    make(1)\n    .build()\n)\n",
            [
                ("ACTH001", 2),
            ],
            id="unanchored-multiline-flagged",
        ),
        pytest.param(
            "value = (\n    (make(1))  # well-actually: multi-line\n    .build()\n)\n",
            [],
            id="canonical-anchored-clean",
        ),
        pytest.param(
            "value = (\n    make(1)  # well-actually: multi-line\n    .build()\n)\n",
            [
                ("ACTH001", 2),
            ],
            id="single-segment-bare-base-flagged",
        ),
        pytest.param(
            "value = (\n    resolved  # well-actually: multi-line\n    .relative_to(directory)\n    .as_posix()\n)\n",
            [
                ("ACTH001", 2),
            ],
            id="two-call-two-dot-bare-base-flagged",
        ),
        pytest.param(
            "value = make(1)\n",
            [],
            id="single-invocation-clean",
        ),
        pytest.param(
            "value = obj.attr.other\n",
            [],
            id="call-free-attribute-walk-clean",
        ),
        pytest.param(
            'label = f"{make(1).build()}"\n',
            [],
            id="fstring-interpolation-exempt",
        ),
        pytest.param(
            "value = make(1)  # well-actually: multi-line\n",
            [
                ("ACTH001", 1),
            ],
            id="stale-anchor-flagged",
        ),
        pytest.param(
            "run(make(1).build().tokens, check=False)\n",
            [
                ("ACTH001", 1),
            ],
            id="argument-position-flagged",
        ),
        pytest.param(
            "value = (\n    make(1)  # well-actually: multi-line\n    .build().render()\n)\n",
            [
                ("ACTH001", 2),
            ],
            id="anchored-but-calls-share-a-line-flagged",
        ),
        pytest.param(
            "value = obj.page.get_by_role(name).click()\n",
            [
                ("ACTH001", 1),
            ],
            id="attribute-receiver-short-chain-flagged",
        ),
        pytest.param(
            "value = (\n    (obj.page)  # well-actually: multi-line\n    .get_by_role(name)\n    .click()\n)\n",
            [],
            id="attribute-receiver-parenthesized-base-clean",
        ),
        pytest.param(
            "value = (\n    obj.page  # well-actually: multi-line\n    .locator(x)\n    .get_by_text(y)\n    .click()\n)\n",
            [],
            id="attribute-receiver-long-chain-bare-base-clean",
        ),
        pytest.param(
            "value = obj.foo().b.bar()\n",
            [
                ("ACTH001", 1),
            ],
            id="interspersed-attribute-chain-flagged",
        ),
        pytest.param(
            "value = (\n    (obj)  # well-actually: multi-line\n    .foo()\n    .b.bar()\n)\n",
            [],
            id="interspersed-attribute-parenthesized-clean",
        ),
        pytest.param(
            "value = (\n    obj  # well-actually: multi-line\n    .a()\n    .b()\n    .c\n)\n",
            [],
            id="attribute-terminated-bare-clean",
        ),
    ],
)
def test_chain_layout_outline(source: str, expected: list[tuple[str, int]]) -> None:
    assert outline(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "value = make(1).build()\n",
            "value = (\n    (make(1))  # well-actually: multi-line\n    .build()\n)\n",
            id="wraps-assignment-chain",
        ),
        pytest.param(
            "def f():\n    return make(1).build()\n",
            "def f():\n    return (\n        (make(1))  # well-actually: multi-line\n        .build()\n    )\n",
            id="wraps-return-chain",
        ),
        pytest.param(
            "value = (\n    make(1)  # well-actually: multi-line\n    .build()\n)\n",
            "value = (\n    (make(1))  # well-actually: multi-line\n    .build()\n)\n",
            id="parenthesizes-single-segment-base",
        ),
        pytest.param(
            "value = (\n    make(1).build().render()\n)\n",
            "value = (\n    make(1)  # well-actually: multi-line\n    .build()\n    .render()\n)\n",
            id="relayouts-parenthesized-chain",
        ),
        pytest.param(
            "run(make(1).build().tokens, check=False)\n",
            "run(\n    make(1)  # well-actually: multi-line\n    .build()\n    .tokens,\n    check=False,\n)\n",
            id="explodes-enclosing-call-around-argument-chain",
        ),
        pytest.param(
            "value = resolved.relative_to(directory).as_posix()\n",
            "value = (\n    (resolved)  # well-actually: multi-line\n    .relative_to(directory)\n    .as_posix()\n)\n",
            id="parenthesizes-short-chain-base",
        ),
        pytest.param(
            "value = Path(name).resolve().parent.parent\n",
            "value = (\n    Path(name)  # well-actually: multi-line\n    .resolve()\n    .parent.parent\n)\n",
            id="merges-bare-attribute-run",
        ),
        pytest.param(
            "run(\n    make(1).build().tokens,\n    check=False,\n)\n",
            "run(\n    make(1)  # well-actually: multi-line\n    .build()\n    .tokens,\n    check=False,\n)\n",
            id="relayouts-chain-inside-multiline-call",
        ),
        pytest.param(
            "value = make(1).build()  # keep\n",
            "value = (\n    (make(1))  # well-actually: multi-line\n    .build()\n)  # keep\n",
            id="trailing-comment-rides-the-close",
        ),
        pytest.param(
            "value = (\n    make(1)\n    .build()  # keep\n    .render()\n)\n",
            "value = (\n    make(1)\n    .build()  # keep\n    .render()\n)\n",
            id="foreign-comment-inside-chain-reported-only",
        ),
        pytest.param(
            "value = make([\n    1,\n]).build()\n",
            "value = make([\n    1,\n]).build()\n",
            id="multiline-argument-reported-only",
        ),
        pytest.param(
            "value = make(1)  # well-actually: multi-line\n",
            "value = make(1)\n",
            id="strips-stale-anchor",
        ),
        pytest.param(
            "value = (\n    (make(1))  # well-actually: multi-line\n    .build()\n)\n",
            "value = (\n    (make(1))  # well-actually: multi-line\n    .build()\n)\n",
            id="canonical-chain-untouched",
        ),
        pytest.param(
            "value = obj.page.get_by_role(name).click()\n",
            "value = (\n    (obj.page)  # well-actually: multi-line\n    .get_by_role(name)\n    .click()\n)\n",
            id="parenthesizes-attribute-receiver-short-chain",
        ),
        pytest.param(
            "value = obj.page.locator(x).get_by_text(y).click()\n",
            "value = (\n    obj.page  # well-actually: multi-line\n    .locator(x)\n    .get_by_text(y)\n    .click()\n)\n",
            id="attribute-receiver-long-chain-bare-base",
        ),
        pytest.param(
            "value = obj.foo().b.bar()\n",
            "value = (\n    (obj)  # well-actually: multi-line\n    .foo()\n    .b.bar()\n)\n",
            id="parenthesizes-interspersed-attribute-chain",
        ),
        pytest.param(
            "value = obj.a().b().c().d()\n",
            "value = (\n    obj  # well-actually: multi-line\n    .a()\n    .b()\n    .c()\n    .d()\n)\n",
            id="long-n-call-chain-stays-bare",
        ),
        pytest.param(
            "value = obj.a().b().c\n",
            "value = (\n    obj  # well-actually: multi-line\n    .a()\n    .b()\n    .c\n)\n",
            id="attribute-terminated-chain-stays-bare",
        ),
        pytest.param(
            "value = x[0].foo().bar()\n",
            "value = (\n    x[0]  # well-actually: multi-line\n    .foo()\n    .bar()\n)\n",
            id="subscript-receiver-two-call-stays-bare",
        ),
    ],
)
def test_chain_layout_formatting(source: str, expected: str) -> None:
    assert format_source(source) == expected


@pytest.mark.parametrize(
    ("source",),
    [
        pytest.param(
            "value = make(1).build().render()\nrun(make(2).clean().tokens, check=False)\n",
            id="mixed-chain-shapes",
        ),
        pytest.param(
            "value = (\n    make(1)  # well-actually: multi-line\n    .build().render()\n)\n",
            id="mislaid-anchored-chain",
        ),
    ],
)
def test_chain_formatting_is_idempotent(source: str) -> None:
    once = format_source(source)

    assert format_source(once) == once
