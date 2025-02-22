from datetime import datetime,timedelta
import asyncio
import pytz
import matplotlib.pyplot as plt
from typing import List
from collections import deque
import numpy as np
import pandas as pd

from .renderer import AbstractRenderer
from ..managers.portfolio import PortfolioManager
from ..exchanges.responses import TickerResponse
from ..utils.speed_analyser import SpeedAnalyser

text_kwargs = dict(ha='center', va='center', fontsize=28, color='C1')

class PerformanceChartRenderer(AbstractRenderer):
    def __init__(self, pairs, quote_asset, title = "Performance Chart", plot = False) -> None:
        super().__init__()
        self.quote_asset = quote_asset
        self.pairs = pairs
        self.title = title
        self.plot = plot

    async def reset(self, seed = None):
        self.infos_manager = self.get_trading_env().infos_manager
        self.memory = deque()
        
    async def render_step(self, *args, **kwargs):
        pass

    async def render_episode(self):

        # 1. Transform historical_infos into a DataFrame
        records = []
        for date, infos in self.infos_manager.historical_infos.items():
            records.append(infos)

        # Create and sort DataFrame by date
        df = pd.DataFrame(records).sort_values("date").reset_index(drop=True)

        # 2. Extract relevant columns
        dates = df["date"]
        valuations = df["portfolio_valuation"].values
        actions = df["action"].values
        rewards = df["reward"].values
        
        # We can also reference pair prices directly by columns, for example:
        # df[f"price_{pair}"]
        
        # 3. Compute intervals and metrics
        valuation_asset = df["portfolio_valuation_asset"].iloc[0]
        elapsed_time = dates.iloc[-1] - dates.iloc[0]
        mean_interval = elapsed_time / (len(df) - 1)
        
        # Portfolio Return
        portfolio_return = (max(valuations[-1], 0) - valuations[0]) / valuations[0]
        annualized_portfolio_return = (1 + portfolio_return) ** (
            timedelta(days=365.25) / elapsed_time
        ) - 1
        
        # Market Returns
        annualized_market_returns = {}
        for pair in self.pairs:
            pair_prices = df[f"price_{pair}"].values
            market_returns = (pair_prices[-1] - pair_prices[0]) / pair_prices[0]
            annualized_market_returns[pair] = (1 + market_returns) ** (
                timedelta(days=365.25) / elapsed_time
            ) - 1
        
        # Sharpe Ratio
        all_returns = np.diff(valuations) / valuations[:-1]
        sharpe_ratio = np.mean(all_returns) / (np.std(all_returns) + 1e-6)
        sharpe_ratio *= (timedelta(days=365.25) / mean_interval) ** 0.5

        # 4. (Optional) Plot results if self.plot is True
        if self.plot:
            fig, ax = plt.subplots(1, 1, figsize=(6, 1.5), dpi=300)
            
            # Plot Portfolio Valuation
            ax.tick_params(axis="both", labelsize=5)
            ax.plot(
                dates, valuations,
                color="navy", linewidth=0.7, label="Portfolio Valuation"
            )

            # Plot each pair's normalized price
            for pair in self.pairs:
                pair_prices = df[f"price_{pair}"].values
                ax.plot(
                    dates,
                    pair_prices * valuations[0] / pair_prices[0],
                    linewidth=0.7,
                    label=f"Price of {pair}"
                )
            
            ax.set_yscale("log")
            ax.set_title(self.title)
            ax.grid(color="lightgray", linestyle="--", linewidth=0.5)
            fig.legend(loc="lower center", fontsize=6)
            plt.show()

        # 5. Print summary metrics
        print(
            
            f"{color.BOLD}Date : {dates.iloc[-1].strftime('%d/%m/%Y %H:%M')}",
            f"Valuation : {valuations[-1]:0.2f} {valuation_asset}",
            f"Sharpe Ratio : {sharpe_ratio:0.2f}",
            f"Annualized Portfolio Return : {100*annualized_portfolio_return:0.2f}%",
            *[
                f"Annualized {pair} Return : {100*annualized_market_returns[pair]:0.2f}%"
                for pair in self.pairs
            ],
            color.END,
            sep="\t"
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