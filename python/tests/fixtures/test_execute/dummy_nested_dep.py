import math


def dummy_nested_dep_func(a: int, b: int) -> float:
    try:
        return math.sqrt(a * a - b * b)
    except ValueError as _:
        return math.sqrt(a * a + b * b)
