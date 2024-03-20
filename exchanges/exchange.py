from abc import ABC, abstractmethod, abstractproperty
from decimal import Decimal
from datetime import datetime

from ..core import Pair, Quotation, Portfolio

from .responses import OrderResponse, TickerResponse
from .exceptions import PairNotFound

class AbstractExchange(ABC):    
    @abstractmethod
    async def get_ticker_at_date(self, pair : Pair, date_close : datetime) -> TickerResponse:
        ...
    
    @abstractmethod
    async def get_available_pairs(self) -> list[Pair]:
        ...
    
    @abstractmethod
    async def get_ticker(self, pair : Pair) -> TickerResponse:
        ...

    async def get_quotation(self, pair : Pair) -> Quotation:
        try:
            return (await self.get_ticker(pair = pair)).price
        except PairNotFound as e:
            return (await self.get_ticker(pair = pair.reverse())).price.reverse()
    
    @abstractmethod
    async def get_portfolio(self) -> Portfolio:
        ...

    @abstractmethod
    async def market_order(self, quantity : Decimal, pair : Pair) -> OrderResponse:
        ...


