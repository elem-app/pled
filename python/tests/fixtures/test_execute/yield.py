from typing import Generator


def f1():
    counter = 0
    for i in f2():
        if i > 0:
            counter += 1

    return counter


def f2() -> Generator[int, None, int]:
    yield 1
    yield 2
    return 0


async def f3():
    counter = 0
    async for i in f4():
        counter += i

    return counter


async def f4():
    yield 1
    yield 2
    yield 3


def f5():
    it = f6()
    _ = next(it)
    return sum(it)


def f6() -> Generator[int, None, None]:
    yield from f7()
    yield from [2, 3, 4]


def f7():
    yield 1


def f8():
    x = f9()
    next(x)
    return x.send(2)


def f9() -> Generator[int, int, None]:
    r = yield 1
    yield r
