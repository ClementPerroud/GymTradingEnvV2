#cython: language_level=3
# value.pyx

from copy import copy
from .asset cimport Asset
from .value cimport Value  # for typed returns

cdef double tolerance = 1E-8

cdef class QuoteMismatchError(Exception):
    pass

cdef void _asset_check(Asset asset1, Asset asset2):
    if not (asset1.name == asset2.name):
        raise QuoteMismatchError(f"Cannot add Values with different assets: {asset1} != {asset2}")

cdef class Value:
    """
    Example extension type representing a numeric amount tied to an Asset.
    """
    def __cinit__(self, double amount, Asset asset):

        self.amount = amount
        self.asset = asset

    property asset:
        def __get__(self):
            return self.asset
        
    property amount:
        def __get__(self):
            return self.amount
        def __set__(self, double new_value):
            self.amount = new_value
    
    cpdef Value copy(self):
       return Value(self.amount, self.asset)

    cpdef bint is_null(self):
        return (abs(self.amount) < tolerance)

    def __repr__(self):
        return f"{self.amount} {self.asset}"

    def __add__(self, object other):
        if other is None:
            return self
        if isinstance(other, Value):
            _asset_check(self.asset, other.asset)
            new_value = Value(self.amount + other.amount, self.asset)
            return new_value
        return NotImplemented

    def __neg__(self):
        return Value(-self.amount, self.asset)

    def __sub__(self, object other):
        if isinstance(other, Value):
            neg_other = (<Value>other).__neg__()
            return self.__add__(neg_other)
        return NotImplemented
        
    def __mul__(self, object other):
        if isinstance(other, float) or isinstance(other, int):
            return Value(self.amount * other, self.asset)
        return NotImplemented

    def __rmul__(self, object other):
        return self.__mul__(other)

    def __truediv__(self, object other):
        if isinstance(other, Value):
            return self.amount / other.amount
        if isinstance(other, float) or isinstance(other, int):
            return Value(self.amount / other, self.asset)
        return NotImplemented

    def __abs__(self):
        if self.amount < 0:
            return self.__neg__()
        return self

    def __eq__(self, object other):
        if not isinstance(other, Value):
            return False
        cdef Value o = <Value>other
        if self.asset != o.asset:
            return False
        return abs(self.amount - o.amount) < tolerance

    def __lt__(self, object other):
        if not isinstance(other, Value):
            return False
        cdef Value o = <Value>other
        _asset_check(self.asset, o.asset)
        return self.amount < o.amount

    def __le__(self, object other):
        return self.__eq__(other) or self.__lt__(other)

    def __hash__(self):
        return hash((self.amount, self.asset))
