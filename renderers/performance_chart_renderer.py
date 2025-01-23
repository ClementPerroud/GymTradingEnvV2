from datetime import datetime,timedelta
import asyncio
import matplotlib.pyplot as plt
from typing import List
from collections import deque
import numpy as np

from .renderer import AbstractRenderer
from ..managers.portfolio import PortfolioManager
from ..exchanges.responses import TickerResponse
from ..utils.speed_analyser import SpeedAnalyser

text_kwargs = dict(ha='center', va='center', fontsize=28, color='C1')

class PerformanceChartRenderer(AbstractRenderer):
    def __init__(self, pairs, quote_asset, title = "Performance Chart") -> None:
        super().__init__()
        self.quote_asset = quote_asset
        self.pairs = pairs
        self.portfolio_manager = PortfolioManager(quote_asset= self.quote_asset)
        self.title = title

    async def reset(self, seed = None):
        self.exchange_manager = self.get_trading_env().exchange_manager
        self.time_manager = self.get_trading_env().time_manager
        self.memory = deque()
        
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
            "portfolio_valuation" : float(portfolio_valuation.amount),
            "reward" : reward,
            "trainable" : trainable,
            **{f"price_{pair}" : float(ticker_dict[pair].close.amount) for pair in self.pairs}
        })

    async def render_episode(self):
        if len(self.memory) <= 1: return

        # Extracting data from memory deque
        dates, valuations, rewards = [], [], []
        pair_prices = {pair : [] for pair in self.pairs}
        for index, elem in enumerate(self.memory):
            # if index < 1500 or index > 1700: continue
            dates.append(elem["date"])
            valuations.append(elem["portfolio_valuation"])
            rewards.append(elem["reward"] if elem["trainable"] else 0)
            for pair in self.pairs:
                pair_prices[pair].append(elem[f"price_{pair}"])
        

        valuations = np.array(valuations)

        # Analysing and computation of :
        # Annualized Portfolio Return, Annualized Market Returns, Sharpe Ratio
        elapsed_time = dates[-1] - dates[0]
        mean_interval = (elapsed_time / (len(dates)-1) )

        # Portfolio Return 
        portfolio_return = (valuations[-1] - valuations[0]) / (valuations[0])
        annualized_portfolio_return = (1+portfolio_return) ** (timedelta(days=365.25) / elapsed_time) - 1
        
        # Market Returns
        annualized_market_returns = {}
        for pair in self.pairs:
            market_returns = (pair_prices[pair][-1] - pair_prices[pair][0]) / (pair_prices[pair][0])
            annualized_market_returns[pair] = (1+market_returns) ** (timedelta(days=365.25) / elapsed_time) - 1
        
        # Sharpe Ratio
        all_returns = np.diff(valuations) / valuations[:-1]
        sharpe_ratio = np.mean(all_returns) / (np.std(all_returns) + 1E-6)
        sharpe_ratio *= (timedelta(days = 365.25) / mean_interval)**(0.5)

        # # Display of graphs
        # fig, ax = plt.subplots(1, 1, figsize = (6, 1.5), dpi =300)
        
        # # Plot Portfolio Valuation
        # ax.tick_params(axis='both', labelsize=5)
        # ax.plot(
        #     dates,valuations,
        #     color = "navy", linewidth = 0.7, label = "Portfolio Valuation"
        # )

        # for pair in self.pairs:
        #     ax.plot(
        #         dates,
        #         np.array(pair_prices[pair])*valuations[0]/pair_prices[pair][0],
        #         linewidth = 0.7, label = f"Price of {pair}"
        #     )
        # ax.set_yscale("log")
        # ax.set_title(self.title)
        # ax.grid(color='lightgray', linestyle='--', linewidth=0.5)
        # fig.legend(loc = "lower center", fontsize = 6)
        # plt.show()

        print(
            color.BOLD,
            f"Sharpe Ratio : {sharpe_ratio:0.2f}\t",
            f"Annualized Portfolio Return : {100*annualized_portfolio_return:0.2f}%\t",
            *[f"Annualized {pair} Return : {100*annualized_market_returns[pair]:0.2f}%\t" for pair in self.pairs],
            end= color.END + "\n"
        )


class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'