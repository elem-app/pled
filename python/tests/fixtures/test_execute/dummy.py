def dummy_func(flag: int) -> None:
    from .dummy_dep import dummy_dep_func

    if flag > 0 and dummy_dep_func(1, 1) == 0:
        value = dummy_dep_func(1, 2)
        print(f"flag is positive, calculated {value}")
    elif flag == 0:
        print("flag is zero")
    else:
        print("flag is negative")


dummy_func(1)
dummy_func(0)
dummy_func(flag=-1)
