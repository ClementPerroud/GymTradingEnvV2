#cython: language_level=3
# pair.pyx

from .asset cimport Asset  # cimport extension type from .pxd

cdef class Pair:
    """
    Pair extension type: (asset, quote_asset).
    """
    def __cinit__(self, Asset asset, Asset quote_asset):
        self.asset = asset
        self.quote_asset = quote_asset
        if self.asset == self.quote_asset:
            raise ValueError(f"quote_asset must differ from asset {asset!r}")

    property asset:
        def __get__(self):
            return self.asset
    property quote_asset:
        def __get__(self):
            return self.quote_asset

    cpdef Pair reverse(self):
        # Create a new Pair with reversed assets
        cdef Pair newpair = Pair(self.quote_asset, self.asset)
        return newpair

    def __eq__(self, object other):
        if not isinstance(other, Pair):
            return False
        cdef Pair p = <Pair>other
        return (self.asset == p.asset) and (self.quote_asset == p.quote_asset)

    def __hash__(self):
        return hash((self.asset, self.quote_asset))

    def __repr__(self):
        return f"{self.asset}{self.quote_asset}"
