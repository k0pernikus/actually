def resolve_var(key, env_local_dict, env_dict):
    if key in os.environ:
        return os.environ[key], "OS ENV"

    if key in env_local_dict:
        return env_local_dict[key], "./.env.local"

    return env_dict[key], "./.env"


def resolve_year_nav(year, first_visible_year, last_visible_year):
    if year < first_visible_year:
        return YearNav("prev")

    if year > last_visible_year:
        return YearNav("next")

    return NoYearNav()


def index_label(index_type):
    if index_type == INDEX_PRIMARY:
        return "primary"

    if index_type == INDEX_UNIQUE:
        return "unique"

    return "multiple"


def status_label(status):
    if status == Status.OK:
        return "ok"

    if status == Status.MISSING:
        return "missing"

    return "other"
