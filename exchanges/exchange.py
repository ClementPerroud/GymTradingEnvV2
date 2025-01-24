from abc import ABC, abstractmethod, abstractproperty
from decimal import Decimal
from datetime import datetime
from typing import List

from ..core import Pair, Quotation, Portfolio, Value
from ..element import AbstractEnvironmentElement
from .responses import OrderResponse, TickerResponse
from .exceptions import PairNotFound
from ..utils.speed_analyser import astep_timer
from ..utils.async_lru import alru_cache

class AbstractExchange(AbstractEnvironmentElement, ABC):
    @property
    def order_index(self):
        return -100
    
    @abstractmethod
    async def get_available_pairs(self) -> List[Pair]:
        ...
    
    @abstractmethod
    async def get_ticker(self, pair : Pair, date : datetime = None) -> TickerResponse:
        ...

    @astep_timer("Quotation")
    @alru_cache(maxsize=1_000)
    async def get_quotation(self, pair : Pair, date : datetime = None) -> Quotation:
        try:
            return (await self.get_ticker(pair = pair, date= date)).price
        except PairNotFound as e:
            return (await self.get_ticker(pair = pair.reverse(), date= date)).price.reverse()
    
    @abstractmethod
    async def get_portfolio(self) -> Portfolio:
        ...

    @abstractmethod
    async def market_order(self, quantity : Value, pair : Pair) -> OrderResponse:
        ...