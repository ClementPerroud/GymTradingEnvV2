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
            Tuple[bool , bool]: Return terminated, truncated, trainable
        """
        ...

def ender_deep_search(element) -> List[AbstractEnder]:
    return class_deep_search(
        condition = lambda element : isinstance(element, AbstractEnder),
        element= element,
        list_to_fill= [],
        visited= [],
        excluded= [element]
    )

def element_deep_search(element, excluded = []) -> List[AbstractEnvironmentElement]:
    return class_deep_search(
        condition = lambda element : isinstance(element, AbstractEnvironmentElement),
        element= element,
        list_to_fill= [],
        visited= [],
        excluded = excluded + [element]
    )

