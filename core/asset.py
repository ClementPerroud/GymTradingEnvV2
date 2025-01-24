class Asset(object):

    def __init__(self, name : str):
        self.name = name

    def __eq__(self, other) -> bool:
        if not isinstance(other, Asset): return False
        return self.name == other.name

    def __repr__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return self.__repr__().__hash__()