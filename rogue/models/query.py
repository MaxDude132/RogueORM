class Lookup:
    comparison = "equal"

    def __init__(self, obj, value) -> None:
        self.parent = obj
        self.value = value


class InLookup(Lookup):
    comparison = "in"
