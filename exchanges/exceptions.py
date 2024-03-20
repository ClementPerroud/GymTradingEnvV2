from ..core import Pair

class PairNotFound(Exception):
    def __init__(self, pair : Pair) -> None:
        super().__init__(f"The pair {pair} does not exist in the Echange.")