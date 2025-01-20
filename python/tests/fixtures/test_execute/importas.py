def f1():
    from . import dummy_nested_dep as dnd

    dnd.dummy_nested_dep_func(3, 4)


f1()


def f2():
    from .dummy_nested_dep import dummy_nested_dep_func as f

    f(3, 4)


f2()
