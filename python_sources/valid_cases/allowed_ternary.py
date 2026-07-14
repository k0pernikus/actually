def weather_action(is_sunny_weather):
    return "go_to_beach" if is_sunny_weather else "stay_home"


def scoped_name(name, scope, plain):
    return name if plain else f"{scope}::{name}"


def chosen_greeting(formal):
    greeting = "good_day" if formal else "hey"

    return greeting


def display_label(label, fallback, missing):
    return fallback if missing else f"{label}"
