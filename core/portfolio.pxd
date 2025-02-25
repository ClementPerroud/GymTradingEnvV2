# portfolio.pxd

from typing import Dict  # This won't be used at compile time, just doc
from .asset cimport Asset
from .value cimport Value

cdef class Portfolio(Asset):
    cdef dict _positions
    cpdef dict to_record(self)
    cpdef Value get_position(self, Asset asset)
    cpdef list get_positions(self)
    cpdef void add_position(self, Value position)
    cpdef void add_positions(self, list positions)
    cpdef Portfolio copy(self)

cdef class PortfolioExposition(Portfolio):
    pass
