from abc import ABC, abstractmethod
from typing import Any, List
from typing_extensions import Self
import gymnasium as gym
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from .abstract_trading_env import AbstractTradingEnv
from ..time_managers import AbstractTimeManager
from ..exchanges import AbstractExchange
from ..rewards import AbstractReward
from ..actions  import AbstractActionManager
from ..observers  import AbstractObserver
from ..enders import AbstractEnder, CompositeEnder, ender_deep_search

class RLTradingEnv(AbstractTradingEnv):
    instances = {}
    def __init__(self,
            time_manager : AbstractTimeManager,
            exchange_manager : AbstractExchange,
            action_manager : AbstractActionManager,
            observer : AbstractObserver,
            reward : AbstractReward,
            enders : List[AbstractEnder] = []
        ) -> None:
        
        super().__init__(time_manager= time_manager, exchange_manager= exchange_manager, enders= enders)

        self.action_manager = action_manager
        self.observer = observer
        self.reward = reward

        self.action_space = self.action_manager.action_space()
        self.observation_space = self.observer.observation_space()
    

    async def reset(self, date : datetime, seed = None):
        self.__step = 0
        await super().__reset__(date= date, seed = seed)
        return (await self.observer.get_obs()), {}

    async def step(self, action : Any):
        # At t : execute action
        await self.action_manager.execute(action = action)

        # Going from t to t+1
        await super().__step__()
        self.__step += 1

        # At t+1 : Perform checks, get observations, get rewards
        obs = await self.observer.get_obs()
        reward = await self.reward.get()

        ## Perform ender checks with CompositeEnder
        terminated, truncated, trainable = await self.check()
        
        return obs, reward, terminated, truncated, trainable, {}

    

    