from math import log, exp
from datetime import datetime
import asyncio
from decimal import Decimal

from ..core import Asset, Portfolio
from .rewarder import AbstractRewarder
from ..exchanges import AbstractExchange
from ..managers.portfolio import PortfolioManager
from ..time_managers import AbstractTimeManager
from ..checkers import AbstractChecker
from ..settings import SETTINGS

class ComputedDifferentialSharpeRatioRewarder(AbstractRewarder, AbstractChecker):
    def __init__(self, eta : Decimal, initial_portfolio :Portfolio, quote_asset : Asset, multiply_by = 800) -> None:
        super().__init__(multiply_by= multiply_by)
        self.eta = eta
        self.stabilization_steps = int(1 / (self.eta**0.6)) + 10
        self.initial_portfolio = initial_portfolio
        self.quote_asset = quote_asset

    
    async def reset(self, seed = None):
        self.exchange_manager  = self.get_trading_env().exchange_manager
        self.time_manager = self.get_trading_env().time_manager
        self.portfolio_manager = self.get_trading_env().portfolio_manager
        self.last_valuation = await self.__compute_valuation(portfolio= self.initial_portfolio, date= await self.time_manager.get_current_datetime())
        # self.A_last = 0
        # self.B_last = 0
        self.steps = 0
        self.return_mean_tm1 = 0
        self.return_var_tm1 = 0
        self.sharpe_tm1 = 0
          
    async def check(self):
        """The reward need to stabilize before beeing relevant."""
        # Return terminated, truncated, trainable
        if self.steps < self.stabilization_steps:
            return False, False, False
        return False, False, True


    # Called after forward
    async def compute_reward(self):
        # Compute requirements
        current_portfolio, current_datetime = await self.gather(
            self.exchange_manager.get_portfolio(),
            self.time_manager.get_current_datetime() 
        )

        current_valuation = await self.__compute_valuation(
            portfolio= current_portfolio,
            date= current_datetime
        )

        R_current = current_valuation.amount / self.last_valuation.amount - Decimal("1")

        # Avoid forward fill data to poluate our exponential moving average A and B.
        if abs(R_current) < SETTINGS["tolerance"]:
            return 0
        
        # Compute exponential moving MEAN and VAR or the log_return
        value = log(1 + float(R_current))
        return_mean_t = self.return_mean_tm1 * (1 - self.eta) + self.eta * value
        # Formula for exp moving std found :  
        # Paper "Incremental calculation of weighted mean and variance" written by Tony Finch, Feb 2009
        return_var_t = (1 - self.eta)*(self.return_var_tm1 + self.eta*(value - self.return_mean_tm1)**2)

        if return_mean_t > 0:
            sharpe_t = return_mean_t / (return_var_t**0.5)
        else:
            sharpe_t = return_mean_t * (return_var_t**0.5)
            
        reward = sharpe_t - self.sharpe_tm1

        self.return_mean_tm1 = return_mean_t
        self.return_var_tm1 = return_var_t
        self.sharpe_tm1 = sharpe_t
        self.steps += 1
        return reward

    async def __compute_valuation(self, portfolio : Portfolio, date : datetime = None):
        return await self.portfolio_manager.valuation(
            portfolio= portfolio, date= date, quote_asset= self.quote_asset
        )  
    

class MoodyDifferentialSharpeRatioRewarder(AbstractRewarder, AbstractChecker):
    def __init__(self, eta : Decimal, quote_asset : Asset, multiply_by = 800) -> None:
        super().__init__(multiply_by= multiply_by)
        self.eta = eta
        self.stabilization_steps = int(1 / (self.eta ** Decimal('0.6'))) + 10
        self.quote_asset = quote_asset
    
    
    async def reset(self, seed = None):
        self.exchange_manager  = self.get_trading_env().exchange_manager
        self.time_manager = self.get_trading_env().time_manager
        self.portfolio_manager = self.get_trading_env().portfolio_manager

        portfolio = await self.exchange_manager.get_portfolio()
        self.last_valuation = await self.__compute_valuation(portfolio= portfolio, date= await self.time_manager.get_current_datetime())

        self.A_last = Decimal("0")
        self.B_last = Decimal("0")
        self.steps = 0
    
    def get_eta(self) -> Decimal:
        if self.steps >= self.stabilization_steps : return self.eta
        ratio = Decimal.from_float(self.steps / self.stabilization_steps)
        return Decimal("0.1") * (1 - ratio) + self.eta * ratio
          
    async def check(self):
        """The reward need to stabilize before beeing relevant."""
        # Return terminated, truncated
        if self.steps < self.stabilization_steps:
            return False, False, False
        return False, False, True

    # Called after forward
    async def compute_reward(self):
        # Compute requirements
        current_portfolio, current_datetime = await self.gather(
            self.exchange_manager.get_portfolio(),
            self.time_manager.get_current_datetime() 
        )

        current_valuation = await self.__compute_valuation(
            portfolio= current_portfolio,
            date= current_datetime
        )

        return_t = current_valuation.amount / self.last_valuation.amount - Decimal("1")

        # Avoid forward fill data to poluate our exponential moving average A and B.
        if abs(return_t) < SETTINGS["tolerance"]:
            return 0
        
        # In the paper, Rt is the projet and not the return !
        # return_t = (1 + return_t).ln()
        return_t = (current_valuation.amount / self.last_valuation.amount).ln()* 100_000

        delta_A_current = return_t - self.A_last
        delta_B_current = return_t ** 2 - self.B_last

        current_eta = self.get_eta()
        A_current = self.A_last + current_eta * delta_A_current
        B_current = self.B_last + current_eta * delta_B_current


        # Main Formula
        numerator = (self.B_last * delta_A_current - self.A_last * delta_B_current / 2)
        denominator = (self.B_last - self.A_last**2)**Decimal('1.5')
        if denominator > 0:
            reward = numerator / denominator
        else:
            reward = 0
        # Second Formula proposed later in other paper
        # reward = (
        #     ( (self.B_last - self.A_last**2) * delta_A_current - 0.5 * self.A_last * (delta_A_current)**2) 
        #     / (self.B_last - self.A_last**2)**(3/2)
        # )


        # Update for next reward
        self.last_portfolio = current_portfolio
        self.last_valuation = current_valuation
        self.A_last = A_current
        self.B_last = B_current
        
        self.steps += 1
        return float(reward)

    async def __compute_valuation(self, portfolio : Portfolio, date : datetime = None):
        return await self.portfolio_manager.valuation(
            portfolio= portfolio, date= date, quote_asset= self.quote_asset
        )  