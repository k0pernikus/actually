def check(probe):
    x = probe.f()
    if not x:
        return

    y = probe.g(x)
    if not y:
        return


def gated(data):
    n = len(data)
    if n > 10:
        raise ValueError(n)


def parsed_candidates(rows):
    parsed = (parse(row) for row in rows)

    return [candidate for candidate in parsed if candidate is not None]
