import pytest

from actually.suppressions import banned_violations, counted, suppressions


pytestmark = pytest.mark.unit

BANNED = ("TID251",)


def outline(source: str) -> list[tuple[str, int]]:
    return [(violation.rule.code, violation.line) for violation in banned_violations(source, BANNED)]


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "value = read()  # noqa: TID251\n",
            [
                ("ACTS001", 1),
            ],
            id="banned-code-is-reported",
        ),
        pytest.param(
            "value = read()  # noqa: S105\n",
            [],
            id="unbanned-code-is-left-alone",
        ),
        pytest.param(
            "value = read()  # noqa\n",
            [
                ("ACTS001", 1),
            ],
            id="bare-noqa-silences-the-banned-code-too",
        ),
        pytest.param(
            "value = read()  # noqa: S105, TID251\n",
            [
                ("ACTS001", 1),
            ],
            id="banned-code-inside-a-list-is-reported",
        ),
        pytest.param(
            "value = read()  # explain # noqa: TID251\n",
            [
                ("ACTS001", 1),
            ],
            id="directive-later-in-the-comment-is-found",
        ),
        pytest.param(
            'guide = "see # noqa: TID251 in the guide"\n',
            [],
            id="string-literal-is-not-a-suppression",
        ),
        pytest.param(
            'guide = """\n# noqa: TID251\n"""\n',
            [],
            id="multiline-string-is-not-a-suppression",
        ),
        pytest.param(
            "# ruff: noqa: TID251\nvalue = read()\n",
            [
                ("ACTS001", 1),
            ],
            id="file-level-ruff-directive-is-reported",
        ),
        pytest.param(
            "first = read()  # noqa: TID251\nsecond = read()  # noqa: TID251\n",
            [
                ("ACTS001", 1),
                ("ACTS001", 2),
            ],
            id="each-site-is-reported-with-its-own-line",
        ),
    ],
)
def test_banned_suppressions_are_reported(source: str, expected: list[tuple[str, int]]) -> None:
    assert outline(source) == expected


def test_nothing_is_reported_when_no_code_is_banned() -> None:
    assert banned_violations("value = read()  # noqa: TID251\n", ()) == ()


def test_a_comment_without_a_directive_is_not_a_suppression() -> None:
    assert suppressions("value = read()  # explain the call\n") == ()


@pytest.mark.parametrize(
    ("sources", "silenced", "expected"),
    [
        pytest.param(
            ("a = 1  # noqa: E501\n",),
            (),
            [
                ("E501", 1),
            ],
            id="one-code-counted-once",
        ),
        pytest.param(
            (
                "a = 1  # noqa: E501\n",
                "b = 2  # noqa: E501\n",
            ),
            (),
            [
                ("E501", 2),
            ],
            id="counts-accumulate-across-files",
        ),
        pytest.param(
            ("a = 1  # noqa: S105\n",),
            ("S105",),
            [],
            id="silenced-code-is-not-counted",
        ),
        pytest.param(
            ("a = 1  # noqa\n",),
            (),
            [
                ("*", 1),
            ],
            id="bare-noqa-counts-under-the-all-rules-marker",
        ),
    ],
)
def test_suppressions_are_counted_for_the_warning_summary(
    sources: tuple[str, ...],
    silenced: tuple[str, ...],
    expected: list[tuple[str, int]],
) -> None:
    assert [(count.code, count.times) for count in counted(sources, silenced)] == expected
