def resolved_command(key, mapping):
    if key not in mapping:
        raise KeyError(key)

    labels = {
        "a": 1,
        "b": 2,
    }
    command = (
        CommandLine  # well-actually: multi-line
        .of("git")
        .subcommand("config")
        .argument(labels)
    )

    return command


def first_ready(jobs, fallback):
    for job in jobs:
        if job.is_ready():
            return job

    return fallback


mode = "verbose" if debug else "quiet"

report = build(
    {
        "retries": 3,
    },
    check=False,
)
