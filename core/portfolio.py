from typing import Self
from datetime import datetime
from decimal import Decimal
from copy import deepcopy

from ..settings import SETTINGS
from .asset import Asset
from .value import Value


class Portfolio(Asset):
    def __init__(self, positions : list[Value] = [], name : str = None) -> None:
        super().__init__(name = name)
        self._positions : dict[Asset, Value] = {}
        self.add_positions(positions)

    def __str__(self) -> str:
        return f"Portfolio {self.name} ({';'.join([pos.__str__() for pos in self.get_positions()])})"
    
    def get_position(self, asset : Asset) -> Value:
        try:
            return self._positions[asset]
        except KeyError as e:
            return None
        
    def add_position(self, position : Value):
        try:
            self._positions[position.asset] += position
        except KeyError as e:
            self._positions[position.asset] = position

        # Check to delete if empty
        if isinstance(self._positions[position.asset], Value):
            if self._positions[position.asset].is_null():
                del self._positions[position.asset]

    def add_positions(self, positions : list[Value]):
        for position in positions:
            self.add_position(position= position)
        
    def get_positions(self) -> list[Value]:
        return self._positions.values()
    
    def __add__(self, other):
        if isinstance(other, Portfolio):
            return Portfolio(
                positions= list(self.get_positions()) + list(other.get_positions()),
            )
        
        return NotImplemented
    
    def __neg__(self):
        new_portfolio = deepcopy(self)
        for asset, position in new_portfolio._positions.items():
            new_portfolio._positions[asset].amount *= -1
        return new_portfolio
    
    def __sub__(self, other):
        if isinstance(other, Portfolio):
            new_portfolio = deepcopy(self).__add__(other = other.__neg__())
            new_portfolio.name = f"{self.name} - {other.name}"
            return new_portfolio
    
        
class PortfolioExposition(Portfolio):
    def __init__(self, expositions: dict[Asset, Decimal] = []) -> None:
        super().__init__(positions= [Value(amount = percent, asset = asset) for asset, percent in expositions.items()])

        _sum_check = Decimal('0')
        for amount in expositions.values():
            _sum_check += amount
        if abs(_sum_check - Decimal('1')) > SETTINGS["tolerance"]:
            raise ValueError("Expositions must add up to 1")
    
    