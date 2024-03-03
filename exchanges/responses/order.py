from dataclasses import dataclass
from datetime import datetime
from .response import AbstractResponse
from core import Pair, Value, Quotation

@dataclass
class OrderResponse(AbstractResponse):
    pair : Pair
    date : datetime
    original_quantity : Value
    counterpart_quantity : Value
    price : Quotation
    fees : Value

    def __str__(self):
        return f"OrderResponse({'; '.join([f'{key}={value.__str__()}' for key, value in self.__dict__.items()])})"