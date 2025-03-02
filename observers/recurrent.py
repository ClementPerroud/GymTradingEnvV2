import numpy as np
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from gymnasium.spaces import Space, Box, Sequence
from collections import OrderedDict
from copy import deepcopy

from ..time_managers import AbstractTimeManager
from ..utils.speed_analyser import astep_timer
from .observer import AbstractObserver


class RecurrentObserver(AbstractObserver):
    """
    An Observer that returns a 'window' of historical observations
    from an underlying sub_observer. For each new observation time,
    it queries the sub_observer for the last 'window' timesteps.
    """

    def __init__(self, sub_observer: AbstractObserver, window: int, not_trainable_window = None, **kwargs) -> None:
        """
        Parameters
        ----------
        sub_observer : AbstractObserver
            The observer that provides single-step observations.
        window : int
            How many timesteps to look back when forming an observation.
        """
        super().__init__(**kwargs)
        self.sub_observer = sub_observer
        self.window = window
        self.not_trainable_window = not_trainable_window if not_trainable_window is not None else window 

        # Holds date -> observation. We only keep enough entries
        # to serve up to 'window' calls (with some buffer).
        self.memory = OrderedDict()
        self.first = True

    async def reset(self, seed=None) -> None:
        """
        Reset the observer and clear cached memory of past observations.
        """
        self.time_manager = self.get_trading_env().time_manager
        self.infos_manager = self.get_trading_env().infos_manager
        self.memory.clear()

        if self.first:
            self.infos_manager.infos_func.append(self.reccurent_check)
        self.first = False

    @property
    def simulation_warmup_steps(self) -> int:
        """
        The sub_observer may already require some warmup steps.
        We add 'window' to that to ensure we can build a full window.
        """
        return self.sub_observer.simulation_warmup_steps + self.window

    def observation_space(self) -> Space:
        """
        Returns a Box with shape = (window, ...) if sub_observer's
        observation_space is also a Box. Otherwise NotImplemented.
        """
        sub_space = self.sub_observer.observation_space()
        return Sequence(space= sub_space)
        # if isinstance(sub_space, Box):
        #     shape = (self.window,) + sub_space.shape
        #     # Keep dtype, but set low/high to -∞/+∞ by default.
        #     return Box(low=-np.inf, high=np.inf, shape=shape, dtype=sub_space.dtype)
        return NotImplemented

    def _manage_memory(self):
        """
        Remove the oldest entries once the dict grows beyond 4×window.
        We shrink it down to 3×window to leave a small buffer.
        """
        max_size = self.window * 4
        min_size_after_removal = self.window * 3

        if len(self.memory) > max_size:
            to_remove = len(self.memory) - min_size_after_removal
            for _ in range(to_remove):
                # popitem(last=False) pops the *oldest inserted* item
                self.memory.popitem(last=False)


    async def get_obs(self, date: datetime) -> np.ndarray:
        """
        Return a stacked array of shape (window, sub_observer_obs_shape),
        representing the last window timesteps from sub_observer.
        The earliest time is at index [0], the most recent at index [-1].
        """
        if date is None:
            date = await self.time_manager.get_current_datetime()

        # For a "window" W, we want timesteps [W-1, W-2, ..., 0] steps back
        steps_back = range(self.window - 1, -1, -1)

        # 1) Compute all relevant historical dates in parallel

        # tasks = [self.time_manager.get_historical_datetime(step_back=s, relative_date=date) for s in steps_back]
        # window_dates = await self.gather(*tasks)

        window_dates = []
        for s in steps_back:
            window_dates.append(await self.time_manager.get_historical_datetime(step_back=s, relative_date=date))


        # 2) Identify which of those dates we have not cached
        missing_dates = [d for d in window_dates if d not in self.memory]

        # 3) Fetch new observations from the sub_observer for missing dates
        if missing_dates:
            sub_tasks = [self.sub_observer.__get_obs__(date=d) for d in missing_dates]
            new_obs = await self.gather(*sub_tasks)
            # Merge new observations into memory
            for d, obs in zip(missing_dates, new_obs): self.memory[d] = deepcopy(obs)

        # 4) Build result in ascending chronological order
        #    (Because steps_back started from farthest in the past -> to present)
        results = [self.memory[d] for d in window_dates]


        # 5) Remove old entries if memory is too big
        self._manage_memory()

        self.last_window_dates = window_dates

        # 6) Return a list of dict
        return results

    async def reccurent_check(self, infos):
        date = await self.time_manager.get_current_datetime()

        if not infos["trainable"]: return {
            "_reccurent_trainable" : False,
            "trainable" : False
        }

        for window_date in self.last_window_dates[-self.not_trainable_window:]:
            if window_date < date and window_date in self.infos_manager.historical_infos:
                historical_infos = self.infos_manager.historical_infos[window_date]
                if not historical_infos['_reccurent_trainable']:
                    return {
                        "_reccurent_trainable" : True,
                        "trainable" : False
                    }
        return {"_reccurent_trainable" : True, "trainable" : True}
    
