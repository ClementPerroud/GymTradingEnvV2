from datetime import datetime
from gymnasium.spaces import Space, Discrete
from typing import TypeVar, List

from .action_manager import AbstractActionManager
from .action import AbstractAction

ActType = TypeVar("ActType")

class DiscreteActionManager(AbstractActionManager):
    def __init__(self, actions : List[AbstractAction]) -> None:
        super().__init__()
        self.actions = actions
    
    async def execute(self, action : ActType) -> None:
        await super().execute(action=action)
        index = action
        return await self.actions[index].execute()
    
    def action_space(self) -> Space:
        return Discrete(len(self.actions))