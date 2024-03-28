import asyncio
from typing import List

from .ender import AbstractEnder

class CompositeEnder(AbstractEnder):
    def __init__(self) -> None:
        self.enders : List[AbstractEnder] = []

    async def check(self):
        terminated, truncated = False, False
        ender_tasks = []

        async with asyncio.TaskGroup() as tg:
            for ender in self.enders:
                if id(ender) is not id(self): # To avoid infinite loop
                    ender_tasks.append(tg.create_task(ender.check()))

        for ender_task in ender_tasks:
            ender_terminated, ender_truncated = ender_task.result()
            terminated, truncated = (terminated or ender_terminated), (truncated or ender_truncated)
        return terminated, truncated