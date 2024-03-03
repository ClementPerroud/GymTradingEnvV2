from abc import ABC, abstractmethod
from typing import Any, Self
import gymnasium as gym
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from time_managers import AbstractTimeManager
from rewards import AbstractReward
from actions  import AbstractActionManager
from observers  import AbstractObserver
from enders import AbstractEnder, CompositeEnder, ender_deep_search

class TradingEnv(gym.Env, CompositeEnder):
    def __init__(self,
            time_manager : AbstractTimeManager,
            action_manager : AbstractActionManager,
            observer : AbstractObserver,
            reward : AbstractReward,
            enders : list[AbstractEnder] = []
        ) -> None:
        super().__init__()
        self.time_manager = time_manager
        self.action_manager = action_manager
        self.observer = observer
        self.reward = reward

        # Implement enders for CompositeEnder class
        self.enders = ender_deep_search(self) + enders
        self.action_space = self.action_manager.action_space()
        self.observation_space = self.observer.observation_space()


    
    async def reset(self, date : datetime, seed = None):
        self.__step = 0
        super().reset(seed = seed)
        await self.time_manager.reset(date= date)

        # Go though the step needed for the observer to work
        for _ in range(self.observer.observation_lookback):
            await self.time_manager.step()

        return None,  {}
        # return (await self.observer.get_obs()), {}

    async def step(self, action : Any):
        # At t : execute action
        await self.action_manager.execute(action = action)

        # Going from t to t+1
        await self.time_manager.step()
        self.__step += 1

        # At t+1 : Perform checks, get observations, get rewards
        obs = await self.observer.get_obs()
        reward = await self.reward.get()

        ## Perform ender checks with CompositeEnder
        terminated, truncated = await self.check()
        
        return obs, reward, terminated, truncated, {}

    

    