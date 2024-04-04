from abc import ABC

from ..element import AbstractEnvironmentElement

class AbstractRenderer(AbstractEnvironmentElement, ABC):
    def render_step(self, action, next_obs, reward, terminated, truncated, trainable, infos):
        ...
    
    def render_episode(self):
        ...