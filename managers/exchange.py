import asyncio
from functools import lru_cache
from datetime import datetime
from typing import List

from ..element import AbstractEnvironmentElement
from ..exchanges import AbstractExchange
from ..exchanges.responses import OrderResponse
from ..core import Pair, Asset, Value

class ExchangeManager(AbstractEnvironmentElement):
    def __init__(self) -> None:
        pass
    
    async def reset(self, date : datetime, seed = None):
        self.exchange = self.get_trading_env().exchange
        self.pairs = await self.exchange.get_available_pairs()
        # Create a set for unique assets
        self.assets = set()
        for pair in self.pairs:
            self.assets.add(pair.asset)
            self.assets.add(pair.quote_asset)

        # Initialize the graph
        self.graph = {asset: set() for asset in self.assets}
        for pair in self.pairs:
            self.graph[pair.asset].add(pair.quote_asset)
            self.graph[pair.quote_asset].add(pair.asset)  # Assuming you can trade in both directions
        
    
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
    
    async def get_quotation(self, pair : Pair):
        from_asset = pair.asset
        to_asset = pair.quote_asset
        graph_path = self.get_asset_path(from_asset= from_asset, to_asset= to_asset)

        quotation_tasks = []
        async with asyncio.TaskGroup() as tg:
            for i in range(0, len(graph_path)-1):
                intermediate_pair = Pair(graph_path[i], graph_path[i+1])
                quotation_tasks.append(
                    tg.create_task(self.exchange.get_quotation(pair = intermediate_pair))
                )

        quotation = 1
        for quotation_task in quotation_tasks:
            quotation = quotation * quotation_task.result()
            
        return quotation
        


class PathNotFound(Exception):
    def __init__(self, from_asset, to_asset) -> None:
        super().__init__(f"Could not find a path to rally {from_asset} to {to_asset}")

