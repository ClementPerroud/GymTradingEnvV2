from decimal import Decimal
from numbers import Number
from typing import Self
from copy import copy

from .value import Value
from .pair import Pair
from .value import Value, _asset_check

class Quotation:
    def __init__(self, amount : Decimal, pair : Pair):
        # Quotation : e.g 42 012.05 USDT / BTC : amount (asset) / (quote_asset)
        self.amount = amount
        self.pair = pair
        
    
    @property
    def quote_asset(self): return self.pair.quote_asset

    @property
    def asset(self): return self.pair.asset

    def reverse(self) -> Self:
        quotation = copy(self)
        quotation.amount = Decimal('1') / quotation.amount
        quotation.pair = quotation.pair.reverse()
        return quotation
    
    def __str__(self):
        return f"{self.amount : 0.2f} {self.pair.__str__(separator='/')}"

    # Numeric operators
    def __mul__(self, other):
        if isinstance(other, Number):
            other = Decimal(other)
            return Quotation(amount = self.amount * other, pair = self.pair)
        
        if isinstance(other, Value):
            _asset_check(self.asset, other.asset)
            # Quotation : (a / ba)   x   Value : (ba)   =   Value : (a)
            return Value(amount = self.amount * other.amount, asset= self.quote_asset)
        
        if isinstance(other, Quotation):
            # Quotation : Quotation (a / b) x Quotation (b / c) = Quotation (a / c)
            _asset_check(self.quote_asset, other.asset)
            return Quotation(
                amount = self.amount * other.amount,
                pair = Pair(asset = other.asset, quote_asset= self.quote_asset)
            )

        return NotImplemented
    
    def __rmul__(self, other): return self.__mul__(other= other)
    
    def __truediv__(self, other):
        if isinstance(other, Quotation):
            if self.asset == other.asset and self.quote_asset == other.quote_asset:
                return self.amount / other.amount
        return NotImplemented
    
    def __rmul__(self, other):
        return self.__mul__(other = other)
    
    # Comparison operators
    def __eq__(self, other):
        if isinstance(other, Quotation):
            _quotation_check(self, other)
            return self.amount == other.amount
        return NotImplemented
    
    def __lt__(self, other):
        if isinstance(other, Quotation):
            _quotation_check(self, other)
            return self.amount < other.amount
        return NotImplemented
    

def _quotation_check(quotation1 : Quotation, quotation2 : Quotation):
    _asset_check(quotation1.asset, quotation2.asset)
    _asset_check(quotation1.quote_asset, quotation2.quote_asset)

