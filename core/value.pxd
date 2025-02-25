# value.pxd
from decimal import Decimal
from .asset cimport Asset

cdef class Value:
    cdef double amount
    cdef Asset asset
    cpdef bint is_null(self)
    cpdef Value copy(self)

cdef void _asset_check(Asset asset1, Asset asset2)

cdef double tolerance 