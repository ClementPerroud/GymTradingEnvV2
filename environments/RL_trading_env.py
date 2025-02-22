from abc import ABC, abstractmethod
from typing import Any, List
from typing_extensions import Self
import gymnasium as gym
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import asyncio

from .abstract_trading_env import AbstractTradingEnv, Mode
from ..infos_manager import InfosManager
from ..time_managers import AbstractTimeManager
from ..exchanges import AbstractExchange
from ..rewarders import AbstractRewarder
from ..actions  import AbstractActionManager
from ..observers  import AbstractObserver
from ..managers import PortfolioManager
from ..checkers import AbstractChecker
from ..renderers import AbstractRenderer
from ..utils.speed_analyser import SpeedAnalyser, astep_timer

class RLTradingEnv(AbstractTradingEnv):
    instances = {}
    def __init__(self,
            mode : Mode,
            time_manager : AbstractTimeManager,
            exchange_manager : AbstractExchange,
            action_manager : AbstractActionManager,
            observer : AbstractObserver,
            rewarder : AbstractRewarder,
            infos_manager : InfosManager,
            checkers : List[AbstractChecker] = [],
            renderers : List[AbstractRenderer] = [],
        ) -> None:
        
        super().__init__(mode = mode, time_manager= time_manager, exchange_manager= exchange_manager, infos_manager = infos_manager, checkers= checkers, renderers = renderers)

        self.action_manager = action_manager
        self.observer = observer
        self.rewarder = rewarder

        self.action_space = self.action_manager.action_space()
        self.observation_space = self.observer.observation_space()

        self.speed_analyser = SpeedAnalyser()

    

    async def reset(self, seed = None, **kwargs):
        self.__step = 0
        trainable = await super().__reset__(seed = seed, **kwargs)
        obs = await self.observer.__get_obs__()

        return obs, await self.infos_manager.reset_infos(obs = obs, trainable= trainable)

    async def step(self, action : Any):
        # At t : execute action
        await self.action_manager.__execute__(action = action)

        # Going from t to t+1
        await super().__step__()
        self.__step += 1

        # At t+1 : Perform checks, get observations, get rewards
        obs = await self.observer.__get_obs__()

        ## Perform checks
        terminated, truncated, trainable = await self.__check__()


        reward = 0
        if not terminated: reward = await self.rewarder.__get__()

        infos = await self.infos_manager.step_infos(action = action, obs = obs, reward = reward, terminated = terminated, truncated = truncated, trainable = trainable)
        ##  Trigger renderers
        await self.__render__(action, obs, reward, terminated, truncated, infos)

        return obs, reward, terminated, truncated, infos
    

    async def check(self): return False, False, True