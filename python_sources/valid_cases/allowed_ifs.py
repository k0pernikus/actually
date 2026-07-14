def access_level(user, resource):
    if user.is_admin:
        return "admin"

    if resource.is_public:
        return "read"

    return "none"


def is_ready(job):
    if job is None:
        return False

    if not job.has_started():
        return False

    return job.is_complete()


def parsed_port(raw):
    if raw is None:
        raise ValueError("port is required")

    if not raw.isdigit():
        raise ValueError(f"not a number: {raw}")

    return int(raw)


def first_positive(numbers, fallback):
    for number in numbers:
        if number > 0:
            return number

    return fallback
