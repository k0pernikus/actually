command = (
    CommandLine  # well-actually: multi-line
    .of("git")
    .subcommand("config")
    .argument(key)
)

tokens = (
    ConfigGet(key=key)  # well-actually: multi-line
    .command()
    .render()
    .tokens
)

first = (
    make(1)  # well-actually: multi-line
    .build()
    .render()[0]
    .parts
)

completed = run(
    ConfigGet(key=key)  # well-actually: multi-line
    .command()
    .render()
    .tokens,
    check=False,
)

root = (
    (SgRoot(source, "python"))  # well-actually: multi-line
    .root()
)

posix_path = (
    (resolved)  # well-actually: multi-line
    .relative_to(directory)
    .as_posix()
)

repo_root = (
    Path(name)  # well-actually: multi-line
    .resolve()
    .parent.parent
)

result = (
    (CliRunner())  # well-actually: multi-line
    .invoke(
        cli,
        catch_exceptions=False,
    )
)

left = (
    a  # well-actually: multi-line
    .foo()
    .bar()
    .baz()
)

right = (
    (b)  # well-actually: multi-line
    .poit()
    .gnarf()
)

matches = left == right

inline_matches = (
    a  # well-actually: multi-line
    .foo()
    .bar()
    .baz()
) == (
    (b)  # well-actually: multi-line
    .poit()
    .gnarf()
)

if (
    a  # well-actually: multi-line
    .foo()
    .bar()
    .baz()
) == (
    (b)  # well-actually: multi-line
    .poit()
    .gnarf()
):
    handle()

if (
    (make(1))  # well-actually: multi-line
    .build()
    .check()
):
    handle()

plain = make(1)
single = helper(2).clean
