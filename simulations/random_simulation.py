import numpy as np
from datetime import datetime, timedelta
from functools import lru_cache

from .simulation import AbstractPairSimulation

class RandomPairSimulation(AbstractPairSimulation):
    def __init__(self,
            initial_price_amount : float = 1000,  
            year_return = (15/100), # 5% yield / year
            year_std = 15/100,
            memory_size = 1000
        ) -> None:

        self.year_return = year_return
        self.year_std = year_std
        self.initial_price_amount = initial_price_amount
        self.memory_size = memory_size


    
    @lru_cache(maxsize = 50)
    def get_distribution_mean_std(self, interval : timedelta):
        interval_mean = self.year_return * (interval / timedelta(days=365.25))
        interval_std = self.year_std * (np.sqrt(interval / timedelta(days=365.25)))
        return interval_mean, interval_std

    
    async def reset(self, seed = None) -> None:
        self.time_manager = self.get_trading_env().time_manager
        self._date = await self.time_manager.get_current_datetime()
        self.last_close = self.initial_price_amount
        self.get_distribution_mean_std().cache_clear()


    def __compute_next_candle(self, interval : timedelta):
        if interval.total_seconds() <= 0: raise ValueError("interval must be positive.")

        interval_mean, interval_std = self.get_distribution_mean_std(interval = interval)
        _open = self.last_close
        _close = _open * np.random.lognormal(mean = interval_mean, sigma = interval_std)
        _high = max(_open, _close) * ( 1 + abs(1 - np.random.lognormal(mean = 0, sigma = 0.6*interval_std)))
        _low = min(_open, _close) * ( 1 - abs(1 - np.random.lognormal(mean = 0, sigma = 0.6*interval_std)))
        _volume = 1000 * (1 + np.random.lognormal(mean = 0, sigma = 1))

        self.last_close = _close
        return {"open" : _open, "high" : _high, "low" : _low, "close" : _close, "volume" : _volume}
        


    async def forward(self, date : datetime) -> None:
        interval : timedelta = date - self._date
        if abs(interval.total_seconds()) < 1E-5: return

        candle = self.__compute_next_candle(interval= interval)
        self.update_memory(date = date, data = candle)
        self._date = date

