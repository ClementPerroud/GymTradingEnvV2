from abc import ABC, abstractmethod
from datetime import datetime
from utils.class_searcher import class_deep_search

class AbstractEnvironmentElement(ABC):
    async def reset(self, date : datetime):
        pass


def element_deep_search(element) -> list[AbstractEnvironmentElement]:
    return class_deep_search(
        condition = lambda element : isinstance(element, AbstractEnvironmentElement),
        element= element,
        list_to_fill= [],
        visited= []
    )