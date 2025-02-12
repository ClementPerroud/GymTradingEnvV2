from abc import ABC, abstractmethod, abstractproperty
import asyncio
from typing import List, Tuple

from ..element import AbstractEnvironmentElement
from ..utils.speed_analyser import astep_timer

class AbstractEnder(AbstractEnvironmentElement, ABC):
    
    @astep_timer(step_name="Check")
    async def __check__(self, **kwargs) -> Tuple[bool , bool]:
        return await self.check()
    
    @abstractmethod
    async def check(self) -> Tuple[bool , bool]:
        """_summary_

        Returns:
            Tuple[bool , bool]: Return terminated, truncated, trainable
        """
        ...

def ender_deep_search(list_elements : List) -> List[AbstractEnder]:
    return [element for element in list_elements if isinstance(element, AbstractEnder)]


