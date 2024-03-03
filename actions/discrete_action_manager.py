from gymnasium.spaces import Space, Discrete
from .action_manager import AbstractActionManager
from .action import AbstractAction
from typing import TypeVar
ActType = TypeVar("ActType")

class DiscreteActionManager(AbstractActionManager):
    def __init__(self, actions : list[AbstractAction]) -> None:
        super().__init__()
        self.actions = actions

    async def execute(self, action : ActType) -> None:
        index = action
        return await self.actions[index].execute()
    
    def action_space(self) -> Space:
        return Discrete(len(self.actions))