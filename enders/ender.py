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

def ender_deep_search(list_elements : List) -> List[AbstractEnder]:
    return [element for element in list_elements if isinstance(element, AbstractEnder)]


