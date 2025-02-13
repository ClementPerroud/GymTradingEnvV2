import asyncio
from functools import lru_cache
from datetime import datetime
from decimal import Decimal
from typing import List

from ..element import AbstractEnvironmentElement
from ..exchanges import AbstractExchange
from ..exchanges.responses import OrderResponse, TickerResponse
from ..core import Pair, Asset, Value, Portfolio
from ..utils.async_lru import alru_cache

class ExchangeManager(AbstractExchange):
    def __init__(self, exchange : AbstractExchange) -> None:
        self.exchange = exchange
    
    @property
    def order_index(self):
        return super().order_index + 1
    
    async def reset(self, seed = None):
        # Reset cached memory
        # self.get_available_pairs.cache_clear()
        # self.__lru_get_portfolio.cache_clear()
        # self.__lru_get_quotation.cache_clear()
        # self.__lru_get_ticker.cache_clear()
        
        self.time_manager = self.get_trading_env().time_manager
        # Create a set for unique assets
        self.assets = set()
        for pair in await self.get_available_pairs():
            self.assets.add(pair.asset)
            self.assets.add(pair.quote_asset)

        # Initialize the graph
        self.graph = {asset: set() for asset in self.assets}
        for pair in await self.get_available_pairs():
            self.graph[pair.asset].add(pair.quote_asset)
            self.graph[pair.quote_asset].add(pair.asset)  # Assuming you can trade in both directions
        
        # Used for caching portfolio.
        self.nb_orders = 0

    @alru_cache(maxsize=1)
    async def get_available_pairs(self) -> List[Pair]:
        return await self.exchange.get_available_pairs()
    

    async def get_ticker(self, pair : Pair, date : datetime) -> TickerResponse:
        """Use lru_cache to avoid sending twice the same requests."""
        return await self.exchange.get_ticker(pair= pair, date= date)


    async def get_portfolio(self) -> Portfolio:
        """Use lru_cache to avoid sending twice the same requests whereas
        the portfolio did not change (= when no new trade occurs)"""
        return await self.__lru_get_portfolio(nb_orders=self.nb_orders)
    
    @alru_cache(maxsize = 100)
    async def __lru_get_portfolio(self, nb_orders):
        return await self.exchange.get_portfolio()

    
    def get_asset_path(self, from_asset, to_asset) -> List[Asset]:
        """
        Find a path from the pair's asset to its quote asset using BFS
        """
        if from_asset not in self.graph or to_asset not in self.graph:
            raise PathNotFound(from_asset, to_asset)
        
        # Breadth-First Search (BFS) for path finding
        visited = {from_asset}
        queue = [(from_asset, [from_asset])]
        
        while queue:
            current, path = queue.pop(0)
            if current == to_asset:
                return path
            
            for neighbor in self.graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        # Return an empty list if no path is found
        raise PathNotFound(from_asset, to_asset)

        
    async def market_order(self, quantity : Value, pair :Pair) -> List[OrderResponse]:
        if quantity.asset not in [pair.asset, pair.quote_asset]:
            raise ValueError("quantity.quote_asset must match either pair.asset or pair.quote_asset")
        self.nb_orders +=1

        from_asset = pair.asset
        to_asset = pair.quote_asset
        graph_path = self.get_asset_path(from_asset= from_asset, to_asset= to_asset)

        if quantity.asset == to_asset:
            graph_path = graph_path[::-1] 
        
        list_order_responses = []
        for i in range(0, len(graph_path)-1):
            intermediate_pair = Pair(graph_path[i], graph_path[i+1])
            order_response = await self.exchange.market_order(quantity=quantity, pair = intermediate_pair)
            quantity = order_response.counterpart_quantity
            list_order_responses.append(order_response)
        return list_order_responses
    
    async def get_quotation(self, pair : Pair, date : datetime):
        return await self.__lru_get_quotation(pair = pair, date = date)
    
    @alru_cache(maxsize=1_000)
    async def __lru_get_quotation(self, pair : Pair, date : datetime):
        from_asset = pair.asset
        to_asset = pair.quote_asset
        graph_path = self.get_asset_path(from_asset= from_asset, to_asset= to_asset)

        quotation_tasks = []
        for i in range(0, len(graph_path)-1):
            intermediate_pair = Pair(graph_path[i], graph_path[i+1])
            quotation_tasks.append(
                self.exchange.get_quotation(pair = intermediate_pair, date= date)
            )
            
        quotations = await self.gather(*quotation_tasks)

        cumulative_quotation = 1
        for quotation in quotations:
            cumulative_quotation = cumulative_quotation * quotation
            
        return cumulative_quotation
        

class PathNotFound(Exception):
    def __init__(self, from_asset, to_asset) -> None:
        super().__init__(f"Could not find a path to rally {from_asset} to {to_asset}")

