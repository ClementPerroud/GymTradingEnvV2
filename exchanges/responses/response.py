from abc import ABC
from dataclasses import dataclass

@dataclass
class AbstractResponse(ABC):
    status_code : int
    def is_success(self):
        return ((200 <= self.status_code) and (self.status_code <= 299))

