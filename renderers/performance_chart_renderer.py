from datetime import datetime
import asyncio
import matplotlib.pyplot as plt
from typing import List

from .renderer import AbstractRenderer
from ..managers.portfolio import PortfolioManager
from ..exchanges.responses import TickerResponse

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
        self.memory = {}
        
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
        self.memory[date] = {
            "date": date,
            "portfolio" : portfolio,
            "portfolio_valuation" : portfolio_valuation.amount,
            "portfolio_exposition" : portfolio_exposition,
            "reward" : reward,
            "trainable" : trainable,
            **{f"price_{pair}" : ticker_dict[pair].close for pair in self.pairs}
        }

    async def render_episode(self):
        
        fig = plt.figure(figsize = (6, 1.5), dpi = 300)
        dates = list(self.memory.keys())
        initial_valuation = self.memory[min(dates)]["portfolio_valuation"]
        fig, ax = plt.subplots(1, 1, figsize = (6, 1.5), dpi = 800)
        ax.tick_params(axis='both', labelsize=5)
        ax.plot(
            dates,
            [self.memory[date]["portfolio_valuation"] for date in dates],
            color = "navy", linewidth = 0.7, label = "Portfolio Valuation"
        )


        for pair in self.pairs:
            initial_price = self.memory[min(dates)][f"price_{pair}"]
            ax.plot(
                dates,
                [self.memory[date][f"price_{pair}"]*initial_valuation/initial_price for date in dates],
                linewidth = 0.7, label = f"Price of {pair}"
            )
        ax.set_yscale("log")
        ax.grid(color='lightgray', linestyle='--', linewidth=0.5)
        fig.legend(loc = "upper center", fontsize = 6)
        plt.show()
