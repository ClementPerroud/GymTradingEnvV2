from .pair cimport Pair

cdef class Quotation:
    cdef double amount
    cdef Pair pair
    cpdef Quotation reverse(self)
