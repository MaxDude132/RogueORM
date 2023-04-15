class Lookup:
    comparison = "equal"

    def __init__(self, obj, value, tracking) -> None:
        self.parent = obj
        self.value = value
        self.tracking = tracking


class InLookup(Lookup):
    comparison = "in"
