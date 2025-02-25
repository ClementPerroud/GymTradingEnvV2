# pair.pxd
from .asset cimport Asset  # cimport from the pxd
cdef class Pair:
    cdef Asset asset
    cdef Asset quote_asset
    cpdef Pair reverse(self)