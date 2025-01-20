from . import dummy_nested_dep


def dummy_dep_func(a: int, b: int) -> float:
    i = 0
    sum = 0
    while i < 1:
        i += 1
        sum += dummy_nested_dep.dummy_nested_dep_func(a, b)
    return sum
