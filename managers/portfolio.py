from functools import lru_cache
from decimal import Decimal
import asyncio
from datetime import datetime
from typing import Dict, List

from ..exchanges import AbstractExchange
from ..element import AbstractEnvironmentElement
from ..core import Portfolio, PortfolioExposition, Pair, Asset, Value
from ..utils.speed_analyser import astep_timer
from ..utils.async_lru import alru_cache

class PositionManager(AbstractEnvironmentElement):
    def __init__(self,  quote_asset : Asset) -> None:
        self.quote_asset = quote_asset

    async def reset(self, seed = None):
        self.exchange_manager = self.get_trading_env().exchange_manager

    @alru_cache(maxsize=128)
    async def valuation(self, position : Value, date : datetime) -> Value:
        if position.asset == self.quote_asset: return position
        return position * await self.exchange_manager.get_quotation(
            pair = Pair(asset= position.asset, quote_asset= self.quote_asset),
            date= date
        )
    
class PortfolioManager(AbstractEnvironmentElement):
    def __init__(self, quote_asset : Asset) -> None:
        self.quote_asset = quote_asset
        self.position_manager = PositionManager(quote_asset= self.quote_asset)

    async def reset(self, seed = None):
        self.exchange_manager = self.get_trading_env().exchange_manager

    @alru_cache(maxsize=128)
    async def __valuations(self, portfolio : Portfolio, date : datetime) -> Dict[Asset, Value]:
        assets, valuation_tasks = [], []
        for position in portfolio.get_positions():
            assets.append(position.asset)
            valuation_tasks.append(self.position_manager.valuation(position = position, date= date))
        valuations = await self.gather(*valuation_tasks)
        return dict(zip(assets, valuations))
    
    async def valuation(self, portfolio : Portfolio, date : datetime, valuations : Dict[Asset, Value] = None, **kwargs) -> Value:
        if valuations is None: valuations = await self.__valuations(portfolio = portfolio, date= date)
        _sum = Value(Decimal('0'), self.position_manager.quote_asset)
        for value in valuations.values():
            _sum += value
        return _sum
    
    
    @alru_cache(maxsize=128)
    async def exposition(self, portfolio : Portfolio, date : datetime ) -> PortfolioExposition:
        valuations = await self.__valuations(portfolio= portfolio, date=date)
        total_valuation = await self.valuation(portfolio = portfolio, date=date, valuations= valuations)

        return PortfolioExposition(
            expositions = {
                asset : valuation / total_valuation
                for asset, valuation in valuations.items() 
            }
        )


        