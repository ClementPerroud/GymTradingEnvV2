from abc import ABC

from ..element import AbstractEnvironmentElement

class AbstractRenderer(AbstractEnvironmentElement, ABC):
    async def render_step(self, action, next_obs, reward, terminated, truncated, infos):
        ...
    
    async def render_episode(self):
        ...