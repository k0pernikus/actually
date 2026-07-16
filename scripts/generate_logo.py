import colorsys
import io
from pathlib import Path

import rich_click as click
from pyfiglet import Figlet
from rich.console import Console
from rich.text import Text


REPO_ROOT = (
    Path(__file__)  # well-actually: multi-line
    .resolve()
    .parent.parent
)
LOGO_PATH = REPO_ROOT / "src" / "actually" / "logo.ansi"
BANNER_TEXT = "well-actually"
FONT = "slant"
RENDER_WIDTH = 250
READONLY_MODE = 0o444
WRITABLE_MODE = 0o644


@click.command(help="Generate src/actually/logo.ansi — the rainbow banner shown by `actually --version`.")
@click.option(
    "--check",
    "check_only",
    is_flag=True,
    help="Exit 1 when logo.ansi is stale instead of writing.",
)
def main(check_only: bool) -> None:
    rendered = _render_banner()
    if check_only:
        _assert_fresh(rendered)
        click.echo("logo.ansi is fresh")

        return

    _write_readonly(LOGO_PATH, rendered)
    click.echo(f"wrote {LOGO_PATH.relative_to(REPO_ROOT)}")


def _render_banner() -> str:
    figlet = Figlet(font=FONT, width=RENDER_WIDTH)
    raw: str = figlet.renderText(BANNER_TEXT)
    lines = [line.rstrip() for line in raw.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"figlet produced no output for {BANNER_TEXT!r}")

    width = max(len(line) for line in lines)
    buffer = io.StringIO()
    console = Console(file=buffer, force_terminal=True, color_system="256", width=RENDER_WIDTH)
    console.print(_rainbow(lines, width))

    return buffer.getvalue()


def _rainbow(lines: list[str], width: int) -> Text:
    text = Text()
    for line in lines:
        for column, char in enumerate(line):
            text.append(char, style=_hue(column, width))

        text.append("\n")

    return text


def _hue(column: int, width: int) -> str:
    red, green, blue = colorsys.hls_to_rgb(column / width, 0.5, 1.0)

    return f"#{int(red * 255):02x}{int(green * 255):02x}{int(blue * 255):02x}"


def _assert_fresh(rendered: str) -> None:
    if LOGO_PATH.is_file() and LOGO_PATH.read_text(encoding="utf-8") == rendered:
        return

    click.secho("stale: src/actually/logo.ansi", fg="red", err=True)
    click.secho("run: uv run python scripts/generate_logo.py", fg="red", err=True)
    raise SystemExit(1)


def _write_readonly(path: Path, content: str) -> None:
    if path.is_file():
        path.chmod(WRITABLE_MODE)

    path.write_text(content, encoding="utf-8")
    path.chmod(READONLY_MODE)


if __name__ == "__main__":
    main()
