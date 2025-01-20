def f1():
    for _ in f2():
        pass


def f2():
    import time

    while True:
        time.sleep(0.3)
        yield 1
