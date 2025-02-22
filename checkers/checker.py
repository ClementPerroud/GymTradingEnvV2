from abc import ABC, abstractmethod, abstractproperty
import asyncio
from typing import List, Tuple

from ..element import AbstractEnvironmentElement
from ..utils.speed_analyser import astep_timer

class AbstractChecker(AbstractEnvironmentElement, ABC):
    
    @abstractmethod
    async def check(self) -> Tuple[bool , bool, bool]:
        """_summary_

        Returns:
            Tuple[bool , bool]: Return terminated, truncated, trainable
        """
        ...

def checker_deep_search(list_elements : List) -> List[AbstractChecker]:
    return [element for element in list_elements if isinstance(element, AbstractChecker)]


