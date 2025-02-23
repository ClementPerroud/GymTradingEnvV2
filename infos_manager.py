from datetime import datetime,timedelta
import asyncio
import pytz
import matplotlib.pyplot as plt
from typing import List
from collections import deque
import numpy as np

from .core.pair import Pair
from .core.asset import Asset
from .core.portfolio import Portfolio, PortfolioExposition
from .renderers.renderer import AbstractRenderer
from .managers.portfolio import PortfolioManager
from .exchanges.responses import TickerResponse
from .utils.speed_analyser import SpeedAnalyser


class InfosManager(AbstractRenderer):
    def __init__(self, pairs : list[Pair], quote_asset) -> None:
        super().__init__()
        self.quote_asset = quote_asset
        self.pairs = pairs
        self.assets = set([pair.asset for pair in pairs] + [pair.quote_asset for pair in pairs])
        self.infos_func = []

    async def reset(self, seed = None):
        self.exchange_manager = self.get_trading_env().exchange_manager
        self.time_manager = self.get_trading_env().time_manager
        self.portfolio_manager = self.get_trading_env().portfolio_manager
        self.historical_infos = {}

    def add_metric(self, func):
        self.infos_func.append(func)
    
    async def _get_infos(self):
        # Retrieve data
        date = await self.time_manager.get_current_datetime()
        portfolio = await self.exchange_manager.get_portfolio()
        results = await self.gather(
            self.portfolio_manager.valuation(portfolio= portfolio, date= date, quote_asset= self.quote_asset),
            self.portfolio_manager.exposition(portfolio= portfolio, date= date, quote_asset= self.quote_asset),
            *[self.exchange_manager.get_ticker(pair= pair, date=date) for pair in self.pairs],
        )
        portfolio_valuation = results[0]
        portfolio_exposition : PortfolioExposition =  results[1]
        ticker_dict : List[TickerResponse] = dict(zip(self.pairs, results[2:]))

        # Process data
        portfolio_per_asset  = {asset : portfolio.get_position(asset = asset) for asset in self.assets}
        portfolio_exposition_per_asset = {asset : portfolio_exposition.get_position(asset = asset) for asset in self.assets}
        for _dict_per_asset in [portfolio_per_asset, portfolio_exposition_per_asset]:
            for asset in self.assets: 
                if _dict_per_asset[asset] is None: _dict_per_asset[asset] = 0
                else: _dict_per_asset[asset] = _dict_per_asset[asset].amount

        infos = {
            "date": date,
            "portfolio_valuation" : float(portfolio_valuation.amount),
            "portfolio_valuation_asset" : portfolio_valuation.asset.name,
            **{f"portfolio_{asset}" : float(portfolio_per_asset[asset]) for asset in self.assets},
            **{f"position_exposition_{asset}" : float(portfolio_exposition_per_asset[asset]) for asset in self.assets},
            **{f"price_{pair}" : float(ticker_dict[pair].close.amount) for pair in self.pairs},
            "quote_asset" : self.quote_asset.name,
            "assets" : [asset.name for asset in [asset for asset in self.assets if asset != self.quote_asset]],
        }

        return date, infos
    
    async def reset_infos(self, obs, trainable):
        date, infos = await self._get_infos()
        infos.update({
            "trainable" : trainable,
        })
        for infos_func in self.infos_func:
            infos.update(await infos_func(infos=infos))

        self.historical_infos[date] = infos
        return infos
    
    async def step_infos(self, action, obs, reward, terminated, truncated, trainable):
        date, infos = await self._get_infos()
        infos.update({
            "action" : action,
            "reward" : reward,
            "trainable" : trainable,
        })
        for infos_func in self.infos_func:
            result = await infos_func(infos=infos)
            if not isinstance(result, dict):
                print(result)
            infos.update(result)

        self.historical_infos[date] = infos
        return infos