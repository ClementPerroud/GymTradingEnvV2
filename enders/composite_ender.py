import asyncio
from typing import List

from .ender import AbstractEnder

class CompositeEnder(AbstractEnder):
    def __init__(self) -> None:
        self.enders : List[AbstractEnder] = []

    async def check(self):
        terminated, truncated = False, False
        ender_tasks = []

        for ender in self.enders:
            if id(ender) is not id(self): # To avoid recursive call which would lead to an infinite loop
                ender_tasks.append(ender.check())
        ender_results = await asyncio.gather(*ender_tasks)

        for ender_result in ender_results:
            ender_terminated, ender_truncated = ender_result
            terminated, truncated = (terminated or ender_terminated), (truncated or ender_truncated)
        return terminated, truncated