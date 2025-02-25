#cython: language_level=3
# quotation.pyx

from numbers import Number
from copy import copy

from .value cimport Value, _asset_check
from .pair cimport Pair
from .quotation cimport Quotation  # for typed returns

cdef void _quotation_check(Quotation q1, Quotation q2):
    _asset_check(q1.asset, q2.asset)
    _asset_check(q1.quote_asset, q2.quote_asset)

cdef class Quotation:
    def __cinit__(self, double amount, Pair pair):
        self.amount = amount
        self.pair = pair
    
    property amount:
        def __get__(self):
            return self.amount

    property quote_asset:
        def __get__(self):
            return self.pair.quote_asset

    property asset:
        def __get__(self):
            return self.pair.asset

    cpdef Quotation reverse(self):
        cdef double amount = 1 / (self.amount + 1E-9)
        cdef Quotation quo = Quotation(amount, self.pair.reverse())
        return quo

    def __repr__(self):
        return f"{self.amount:0.2f} {self.pair.asset}/{self.pair.quote_asset}"

    def __mul__(self, object other):
        if isinstance(other, float) or isinstance(other, int):
            return Quotation(self.amount * other, self.pair)

        elif isinstance(other, Value):
            val = <Value>other
            _asset_check(self.asset, val.asset)
            return Value(self.amount * val.amount, self.quote_asset)
            # Actually your code returns a Value with self.quote_asset, so:
            # return Value(self.amount * val.amount, self.quote_asset)
        elif isinstance(other, Quotation):
            q = <Quotation>other
            _asset_check(self.quote_asset, q.asset)
            new_amount = self.amount * q.amount
            new_pair = Pair(q.asset, self.quote_asset)
            return Quotation(new_amount, new_pair)
        return NotImplemented

    def __rmul__(self, object other):
        return self.__mul__(other)

    def __truediv__(self, object other):
        if isinstance(other, Quotation):
            q = <Quotation>other
            if (self.asset == q.asset) and (self.quote_asset == q.quote_asset):
                return self.amount / q.amount
        return NotImplemented

    def __eq__(self, object other):
        if not isinstance(other, Quotation):
            return False
        cdef Quotation q = <Quotation>other
        _quotation_check(self, q)
        return self.amount == q.amount

    def __lt__(self, object other):
        if not isinstance(other, Quotation):
            return False
        cdef Quotation q = <Quotation>other
        _quotation_check(self, q)
        return self.amount < q.amount
