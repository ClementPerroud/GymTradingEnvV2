from datetime import datetime
import asyncio
import matplotlib.pyplot as plt
from typing import List

from .renderer import AbstractRenderer
from ..managers.portfolio import PortfolioManager
from ..exchanges.responses import TickerResponse
from ..utils.speed_analyser import SpeedAnalyser

text_kwargs = dict(ha='center', va='center', fontsize=28, color='C1')

class PerformanceChartRenderer(AbstractRenderer):
    def __init__(self, pairs, quote_asset) -> None:
        super().__init__()
        self.quote_asset = quote_asset
        self.pairs = pairs
        self.portfolio_manager = PortfolioManager(quote_asset= self.quote_asset)

    async def reset(self, date : datetime, seed = None):
        self.exchange_manager = self.get_trading_env().exchange_manager
        self.time_manager = self.get_trading_env().time_manager
        self.memory = []
        
    async def render_step(self, action, next_obs, reward, terminated, truncated, trainable, infos):
        date = await self.time_manager.get_current_datetime()
        portfolio = await self.exchange_manager.get_portfolio()
        results = await asyncio.gather(
            self.portfolio_manager.valuation(portfolio= portfolio, date= date),
            self.portfolio_manager.exposition(portfolio= portfolio, date= date),
            *[self.exchange_manager.get_ticker(pair= pair) for pair in self.pairs],
        )
        portfolio_valuation, portfolio_exposition = results[0], results[1]
        ticker_dict : List[TickerResponse] = dict(zip(self.pairs, results[2:]))
        self.memory.append({
            "date": date,
            "portfolio" : portfolio,
            "portfolio_valuation" : portfolio_valuation.amount,
            "portfolio_exposition" : portfolio_exposition,
            "reward" : reward,
            "trainable" : trainable,
            **{f"price_{pair}" : ticker_dict[pair].close for pair in self.pairs}
        })

    async def render_episode(self):
        dates = [x["date"] for x in self.memory]
        initial_valuation = self.memory[0]["portfolio_valuation"]
        fig, ax = plt.subplots(1, 1, figsize = (6, 1.5), dpi =300)
        ax.tick_params(axis='both', labelsize=5)
        ax.plot(
            dates,
            [x["portfolio_valuation"] for x in self.memory],
            color = "navy", linewidth = 0.7, label = "Portfolio Valuation"
        )


        for pair in self.pairs:
            initial_price = self.memory[0][f"price_{pair}"]
            ax.plot(
                dates,
                [x[f"price_{pair}"]*initial_valuation/initial_price for x in self.memory],
                linewidth = 0.7, label = f"Price of {pair}"
            )
        ax.set_yscale("log")
        ax.grid(color='lightgray', linestyle='--', linewidth=0.5)
        fig.legend(loc = "upper center", fontsize = 6)
        plt.show()