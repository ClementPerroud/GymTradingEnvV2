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

    
class PortfolioManager(AbstractEnvironmentElement):
    async def reset(self, seed = None):
        self.exchange_manager = self.get_trading_env().exchange_manager
        self.position_valuation.cache_clear()
        self.__valuations.cache_clear()
        self.valuation.cache_clear()
        self.exposition.cache_clear()


    @alru_cache(maxsize=128)
    async def position_valuation(self, position : Value, date : datetime, quote_asset : Asset) -> Value:
        if position.asset == quote_asset: return position
        return position * await self.exchange_manager.get_quotation(
            pair = Pair(asset= position.asset, quote_asset= quote_asset),
            date= date
        )

    @alru_cache(maxsize=128)
    async def __valuations(self, portfolio : Portfolio, date : datetime, quote_asset : Asset) -> Dict[Asset, Value]:
        assets, valuation_tasks = [], []
        for position in portfolio.get_positions():
            assets.append(position.asset)
            valuation_tasks.append(self.position_valuation(position = position, date= date, quote_asset= quote_asset))
        valuations = await self.gather(*valuation_tasks)
        return dict(zip(assets, valuations))
    
    @alru_cache(maxsize=128)
    async def valuation(self, portfolio : Portfolio, date : datetime, quote_asset : Asset, **kwargs) -> Value:
        valuations = await self.__valuations(portfolio = portfolio, date= date, quote_asset= quote_asset)
        _sum = Value(Decimal('0'), quote_asset)
        for value in valuations.values():
            _sum += value
        return _sum
    
    
    @alru_cache(maxsize=128)
    async def exposition(self, portfolio : Portfolio, date : datetime, quote_asset : Asset) -> PortfolioExposition:
        valuations = await self.__valuations(portfolio= portfolio, date=date, quote_asset= quote_asset)
        total_valuation = Value(Decimal('0'), quote_asset)
        for value in valuations.values():
            total_valuation += value

        return PortfolioExposition(
            expositions = {
                asset : valuation / total_valuation
                for asset, valuation in valuations.items() 
            }
        )


        