from dataclasses import dataclass
from decimal import Decimal

from ...core import Pair
from .response import AbstractResponse


@dataclass
class PairInfoResponse(AbstractResponse):
    pair : Pair
    percent_fees : Decimal
