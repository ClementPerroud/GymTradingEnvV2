from abc import ABC, abstractmethod
from typing import Any, List
from typing_extensions import Self
import gymnasium as gym
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import asyncio

from .abstract_trading_env import AbstractTradingEnv, Mode
from ..time_managers import AbstractTimeManager
from ..exchanges import AbstractExchange
from ..rewarders import AbstractRewarder
from ..actions  import AbstractActionManager
from ..observers  import AbstractObserver
from ..enders import AbstractEnder, CompositeEnder, ender_deep_search
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
            enders : List[AbstractEnder] = [],
            renderers : List[AbstractRenderer] = [],
        ) -> None:
        
        super().__init__(mode = mode, time_manager= time_manager, exchange_manager= exchange_manager, enders= enders)

        self.action_manager = action_manager
        self.observer = observer
        self.rewarder = rewarder
        self.renderers = renderers

        self.action_space = self.action_manager.action_space()
        self.observation_space = self.observer.observation_space()

        self.speed_analyser = SpeedAnalyser()

    

    async def reset(self, seed = None, **kwargs):
        self.__step = 0
        await super().__reset__(seed = seed, **kwargs)
        obs = await self.observer.__get_obs__()
        return obs, {}

    async def step(self, action : Any):
        # At t : execute action
        await self.action_manager.__execute__(action = action)

        # Going from t to t+1
        await super().__step__()
        self.__step += 1

        # At t+1 : Perform checks, get observations, get rewards
        obs = await self.observer.__get_obs__()
        infos = {"date": await self.time_manager.get_current_datetime()}

        ## Perform ender checks with CompositeEnder
        terminated, truncated, trainable = await self.__check__()

        reward = 0
        if not terminated: reward = await self.rewarder.__get__()
        ## Trigger renderers
        await self.__renderers(action, obs, reward, terminated, truncated, trainable, infos)

        return obs, reward, terminated, truncated, trainable, infos

    @astep_timer("Renderers")
    async def __renderers(self, action, obs, reward, terminated, truncated, trainable, infos, **kwargs):
        render_steps, render_episode = [], []
        for renderer in self.renderers: 
            render_steps.append(renderer.render_step(action, obs, reward, terminated, truncated, trainable, infos))
            if terminated or truncated:
                render_episode.append(renderer.render_episode())
        # First : steps
        await self.gather(*render_steps)
        # Secondly : episode 
        await self.gather(*render_episode)
    

    