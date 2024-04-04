
from decimal import Decimal
from typing import Union
from .asset import Asset
from ..settings import SETTINGS

from copy import copy

class Value:
    def __init__(self, amount : Union[Decimal,str], asset: Asset):
        if isinstance(amount, str): amount = Decimal(amount)
        self.amount : Decimal= amount
        self.asset : Asset = asset

        if not isinstance(amount, Decimal):
            raise ValueError("amount must be of type Decimal")
    
    def is_null(self) -> bool:
        return (abs(self.amount) < SETTINGS["tolerance"])
    
    def __repr__(self) -> str:
        return f"{self.amount} {self.asset}"
    
    def __add__(self, other):
        if isinstance(other, Value):
            _asset_check(self.asset, other.asset)
            new_value = copy(self)
            new_value.amount = self.amount + other.amount
            return new_value
        
    def __neg__(self):
        new_value = copy(self)
        new_value.amount *= -1
        return new_value
    
    def __sub__(self, other):
        # return self + (-other)
        return self.__add__(other.__neg__())

    def __mul__(self, other):
        # self._number_check(other)
        if isinstance(other, Decimal):
            new_value = copy(self)
            new_value.amount *= other
            return new_value
        return NotImplemented
    
    def __rmul__(self, other):
        return self.__mul__(other = other)
    
    def __truediv__(self, other):
        if isinstance(other, Value):
            return self.amount / other.amount
        if isinstance(other, Decimal):
            return self.__mul__(Decimal('1')/other)
        return NotImplemented
        
    def __abs__(self):
        if self.amount < 0:
            return self.__neg__()
        return self
    
    def __eq__(self, other):
        if isinstance(other, Value): 
            return (
                self.asset == other.asset 
                and abs(self.amount - other.amount) < SETTINGS["tolerance"]
            )
        return False
    
    def __lt__(self, other):
        if isinstance(other, Value): 
            _asset_check(self.asset, other.asset)
            return self.amount < other.amount
        return NotImplemented

    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)
    
    def __hash__(self) -> int:
        return hash((self.amount, self.asset))
    
def _asset_check(asset1 : Asset, asset2 : Asset):
    if asset1 != asset2:
        raise QuoteMismatchError(asset1 = asset1, asset2 = asset2)

class QuoteMismatchError(BaseException):
    def __init__(self, asset1 : Asset, asset2 : Asset) -> None:
        super().__init__(f"Can not perfrom add operation with different quote asset : {asset1} != {asset2}")