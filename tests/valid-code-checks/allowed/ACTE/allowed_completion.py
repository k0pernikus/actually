def first_even(numbers):
    for number in numbers:
        if number % 2 == 0:
            return number

    return None


def drain(queue):
    while queue.has_items():
        item = queue.pop()
        handle(item)


def load(path):
    try:
        return parse(path)
    except ParseError:
        return None
