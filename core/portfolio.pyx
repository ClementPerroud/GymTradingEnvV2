#cython: language_level=3
# portfolio.pyx

from libc.math cimport abs

# For more advanced typed containers, we might use `cdef dict[Asset, Value]`, but that is not trivial.
from .asset cimport Asset
from .value cimport Value, tolerance
from .portfolio cimport Portfolio, PortfolioExposition

cdef class Portfolio(Asset):
    """
    Inherits from Asset as a cdef class. That means:
      1) We must define a .pxd for Asset so it's known at compile time.
      2) We can call super().__cinit__() if needed.
    """
    def __cinit__(self):
        """
        Called right after object allocation, 
        before the Python-level __init__ is called.
        """
        self._positions = {}

    def __init__(self, positions=None, name=None):
        """
        Python-level constructor. 
        The user can pass `positions` and `name`.
        """
        # Call the parent’s __init__ for the name
        super().__init__(name)
        if positions is not None:
            self.add_positions(positions)

    def __repr__(self):
        cdef list pos_strs = []
        for v in self.get_positions():
            pos_strs.append(repr(v))
        return f"Portfolio {self.name} ({';'.join(pos_strs)})"
    
    cpdef Portfolio copy(self):
        cdef list positions = []
        cdef Value position
        for position in self.get_positions():
            positions.append(position.copy())
        return Portfolio(positions, self.name)

    cpdef Value get_position(self, Asset asset):
        return self._positions.get(asset, None)

    cpdef void add_position(self, Value position):
        cdef Asset a = position.asset
        if a in self._positions:
            self._positions[a] = self._positions[a].__add__(position)
        else:
            self._positions[a] = position

        # # Remove if zero
        # if self._positions[a].is_null():
        #     del self._positions[a]

    cpdef void add_positions(self, list positions):
        # positions is a list of Values
        cdef Value p
        for p in positions:
            self.add_position(p)

    cpdef list get_positions(self):
        return list(self._positions.values())

    def __add__(self, object other):
        # We can accept a Portfolio or return NotImplemented
        if isinstance(other, Portfolio):
            p = <Portfolio>other
            return Portfolio(self.get_positions() + p.get_positions(), None)
        return NotImplemented

    def __neg__(self):
        cdef Portfolio new_portfolio = self.copy()
        for a, val in new_portfolio._positions.items():
            new_portfolio._positions[a].amount = -new_portfolio._positions[a].amount
        return new_portfolio

    def __sub__(self, object other):
        if isinstance(other, Portfolio):
            new_portfolio = (<Portfolio>self).copy().__add__(<Portfolio>other.__neg__())
            new_portfolio.name = self.name
            return new_portfolio
        return NotImplemented

    cpdef dict to_record(self):
        cdef dict record = {}
        for a, v in self._positions.items():
            record[repr(a)] = float(v.amount)
        return record


cdef class PortfolioExposition(Portfolio):
    def __init__(self, expositions=None):
        if expositions is None:
            expositions = {}
        # We must call Portfolio’s cinit explicitly:
        super().__init__(positions=[], name=None)

    def __cinit__(self, dict expositions):
        cdef double _sum_check = 0
        for asset, amt in expositions.items():
            self.add_position(Value(amt, asset))
            _sum_check += amt

        if abs(_sum_check - 1) > tolerance:
            raise ValueError(f"Expositions must add up to 1 (got {_sum_check}).")
