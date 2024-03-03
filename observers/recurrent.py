import numpy as np
from gymnasium.spaces import Space,Box

from .observer import AbstractObserver

class RecurrentObserver(AbstractObserver):
    def __init__(self, observer : AbstractObserver, window : int, global_observation_space : Space = None) -> None:
        super().__init__()
        self.observer = observer
        self.window = window
        self.global_observation_space = global_observation_space
        
    
    def observation_space(self) -> Space:
        if self.global_observation_space is not None:
            return self.global_observation_space
        # Auto determination of the observation_space
        observer_observation_space=  self.observer.observation_space()
        if isinstance(observer_observation_space, Box):
            shape = list(observer_observation_space.shape)[:]
            shape.insert(0, self.window)
            return Box(shape = shape)
        return NotImplemented

    async def get_obs(self) -> np.ndarray:
        raise NotImplementedError()