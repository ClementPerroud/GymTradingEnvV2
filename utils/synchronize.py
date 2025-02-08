import asyncio
import gymnasium as gym
from ..environments.abstract_trading_env import AbstractEnvironmentElement
class SynchronizeEnv(gym.Env):
    instances = {}
    def __init__(self, async_env, *args, **kwargs) -> None:
        self.async_env = async_env
        super().__init__(*args, **kwargs)
    
    @property
    def observation_space(self): return self.async_env.observation_space
    
    @property
    def action_space(self): return self.async_env.action_space

    
    def reset(self, seed = None):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_env.reset(seed = seed))

    def step(self, action):
        loop = asyncio.get_event_loop()
        obs, reward, terminated, truncated, infos = loop.run_until_complete(self.async_env.step(action = action))
        return obs, reward, terminated, truncated, infos

    

    