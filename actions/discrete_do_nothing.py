from .action import AbstractAction

class DiscreteDoNothing(AbstractAction):
    def __init__(self) -> None:
        pass
    
    async def execute(self) -> None:
        return