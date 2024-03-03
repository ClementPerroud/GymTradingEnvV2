from .asset import Asset
# from settings import exchange
from copy import copy
class Pair:
    def __init__(self, asset : Asset, quote_asset : Asset):
        self.asset = asset
        self.quote_asset = quote_asset
        
        if self.quote_asset == self.asset:
            raise ValueError(f"quote_asset of the value must be different from the asset {asset}")
    def reverse(self):
        pair = copy(self)
        pair.asset, pair.quote_asset = pair.quote_asset, pair.asset
        return pair
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Pair):
            return self.asset == other.asset and self.quote_asset == other.quote_asset
        return False
    
    def __hash__(self) -> int:
        return hash((self.asset, self.quote_asset))
    
    def __str__(self, separator = ""):
        return f"{self.asset}{separator}{self.quote_asset}"
    
