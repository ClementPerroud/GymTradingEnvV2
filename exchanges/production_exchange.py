from decimal import Decimal
from datetime import datetime
from copy import deepcopy
from functools import lru_cache
from typing import List

from ..core import Pair, Quotation, Portfolio, Value
from ..simulations.simulation import AbstractPairSimulation
from ..time_managers import AbstractTimeManager

from .responses import OrderResponse, TickerResponse
from .exceptions import PairNotFound
from .exchange import AbstractExchange

class BinanceProductionExchange(AbstractExchange):
    
    async def get_available_pairs(self) -> List[Pair]:
        ...
    
    async def get_ticker(self, pair : Pair, date : datetime = None) -> TickerResponse:
        ...
    
    async def get_portfolio(self) -> Portfolio:
        ...

    async def market_order(self, quantity : Decimal, pair : Pair) -> OrderResponse:
        ...


