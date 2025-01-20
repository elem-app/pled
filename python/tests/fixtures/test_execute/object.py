class Dummy:
    def __init__(self):
        self._x = 1

    @property
    def value(self):
        return self._x


print(Dummy().value)
