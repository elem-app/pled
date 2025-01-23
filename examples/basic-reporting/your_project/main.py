from .dep import dep_func


def entry(flag: int):
    if flag > 0:
        value = dep_func(flag)
        print(f"flag is positive, calculated {value}")
    elif flag == 0:
        print("flag is zero")
    else:
        print("flag is negative")
