#cython: language_level=3
# asset.pyx

cdef class Asset:
    """
    A Cython extension type representing an asset with a name.
    """
    def __cinit__(self):
        """
        Low-level constructor for cdef class. 
        No user arguments here, or minimal ones if needed.
        """
        self.name = None

    def __init__(self, name=None):
        """
        Normal Python-level constructor. The user can pass `name`.
        """
        self.name = name

    def __eq__(self, object other):
        """
        We use cpdef so Python code can call ==, and it's also available at C-level.
        """
        # For a cdef class, we can check if other is the same type (or a subtype).
        if not isinstance(other, Asset):
            return False
        # Safe cast to Asset at C-level
        cdef Asset o = <Asset>other
        return self.name == o.name

    def __repr__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)
