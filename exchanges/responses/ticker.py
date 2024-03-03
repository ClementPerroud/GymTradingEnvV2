from dataclasses import dataclass
from datetime import datetime

from core import Quotation, Value
from .response import AbstractResponse

@dataclass
class TickerResponse(AbstractResponse):
    date_open : datetime
    date_close : datetime
    open : Quotation
    high : Quotation
    low : Quotation
    close : Quotation
    volume : Value
    price : Quotation
