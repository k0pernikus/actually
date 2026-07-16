from importlib.resources import files


def render_logo() -> str:
    resource = files("actually") / "logo.ansi"

    return resource.read_text(encoding="utf-8")
