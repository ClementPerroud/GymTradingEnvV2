from datetime import datetime,timedelta
import asyncio
import pytz
import matplotlib.pyplot as plt
from typing import List
from collections import deque
import numpy as np

from .renderers.renderer import AbstractRenderer
from .managers.portfolio import PortfolioManager
from .exchanges.responses import TickerResponse
from .utils.speed_analyser import SpeedAnalyser


class InfosManager(AbstractRenderer):
    def __init__(self, pairs, quote_asset) -> None:
        super().__init__()
        self.quote_asset = quote_asset
        self.pairs = pairs
        self.infos_func = []

    async def reset(self, seed = None):
        self.exchange_manager = self.get_trading_env().exchange_manager
        self.time_manager = self.get_trading_env().time_manager
        self.portfolio_manager = self.get_trading_env().portfolio_manager
        self.historical_infos = {}

    def add_metric(self, func):
        self.infos_func.append(func)
    
    async def _get_infos(self):
        date = await self.time_manager.get_current_datetime()
        portfolio = await self.exchange_manager.get_portfolio()
        results = await self.gather(
            self.portfolio_manager.valuation(portfolio= portfolio, date= date, quote_asset= self.quote_asset),
            self.portfolio_manager.exposition(portfolio= portfolio, date= date, quote_asset= self.quote_asset),
            *[self.exchange_manager.get_ticker(pair= pair, date=date) for pair in self.pairs],
        )
        portfolio_valuation, portfolio_exposition = results[0], results[1]
        ticker_dict : List[TickerResponse] = dict(zip(self.pairs, results[2:]))
        infos = {
            "date": date,
            "portfolio_valuation" : float(portfolio_valuation.amount),
            "portfolio_valuation_asset" : portfolio_valuation.asset.name,
            "portfolio" : portfolio,
            "position_exposition" : portfolio_exposition,
            **{f"price_{pair}" : float(ticker_dict[pair].close.amount) for pair in self.pairs}
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