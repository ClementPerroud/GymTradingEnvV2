from abc import ABC, abstractmethod, abstractproperty
import asyncio
from typing import List, Tuple

from ..element import AbstractEnvironmentElement
from ..utils.class_searcher import class_deep_search

class AbstractEnder(AbstractEnvironmentElement, ABC):
    @abstractmethod
    async def check(self) -> Tuple[bool , bool, bool]:
        """_summary_

        Returns:
            Tuple[bool , bool]: Return terminated, truncated
        """
        ...
def check_is_ender(element):
    return isinstance(element, AbstractEnder)

def ender_deep_search(element) -> List[AbstractEnder]:
    return class_deep_search(
        condition = lambda element : isinstance(element, AbstractEnder),
        element= element,
        list_to_fill= [],
        visited= [],
        excluded= [element]
    )

