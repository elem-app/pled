async def f1():
    return await f2()


def f2():
    return f3()


async def f3():
    return 2


async def f4():
    if (await f3()) > 0:
        pass
    while (await f5()) > 0:
        pass


counter = 1


async def f5():
    global counter
    counter -= 1
    return counter
