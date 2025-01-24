from decimal import Decimal
import asyncio
from datetime import datetime
from typing import List, Dict

from .action import AbstractAction
from ..managers.portfolio import PortfolioManager
from ..exchanges import AbstractExchange
from ..core import Asset, Pair, Value, PortfolioExposition

class DiscreteExpositionAction(AbstractAction):
    def __init__(self, target_exposition : Dict[Asset, Decimal], quote_asset : Asset):
        self.quote_asset = quote_asset
        self.target_exposition = PortfolioExposition(expositions= target_exposition)
        self.portfolio_manager = PortfolioManager(quote_asset = self.quote_asset)
        
    async def reset(self, seed = None):
        self.exchange_manager = self.get_trading_env().exchange_manager
        self.time_manager = self.get_trading_env().time_manager

    async def execute_order(self, asset_to_decrease : Asset, asset_to_increase : Asset, quantity_quote_asset : Value):
        quote_asset = quantity_quote_asset.asset
        if asset_to_decrease == quote_asset:
                quantity_asset = - quantity_quote_asset
        else:
            quantity_asset = - quantity_quote_asset * (await self.exchange_manager.get_quotation(pair = Pair(asset_to_decrease, quote_asset= quote_asset))).reverse()

        pair = Pair(asset= asset_to_increase, quote_asset= asset_to_decrease)
        await self.exchange_manager.market_order(
            quantity= quantity_asset,
            pair = pair
        )

    async def execute(self):
        current_position = await self.exchange_manager.get_portfolio()
        date = await self.time_manager.get_current_datetime()
        total_valuation, current_exposition = await self.gather(
            self.portfolio_manager.valuation(
                portfolio= current_position,
                date= date
            ),
            self.portfolio_manager.exposition(
                portfolio= current_position,
                date= date
            )
        )
        quote_asset = total_valuation.asset

        diff_exposition = self.target_exposition - current_exposition
        diff_positions_percent = diff_exposition.get_positions()

        # Prepare
        list_position_to_increase : List[Value] = [] # Position to increase
        list_position_to_decrease : List[Value] = [] # Position to decrease
        for position in diff_positions_percent:
            if position.amount > 0: list_position_to_increase.append(position)
            else: list_position_to_decrease.append( - position) # We make them positive

        # Compute how to re equilibrate porfolio
        order_tasks = []
        while len(list_position_to_decrease)>0 and len(list_position_to_increase)>0:
            position_to_decrease : Value = list_position_to_decrease[0]
            position_to_increase : Value = list_position_to_increase[0]

            if position_to_increase.amount < position_to_decrease.amount:
                ratio_quantity = position_to_increase.amount
                list_position_to_decrease[0].amount -= ratio_quantity
                list_position_to_increase.pop(0)
            else:
                ratio_quantity = position_to_decrease.amount
                list_position_to_decrease.pop(0)
                list_position_to_increase[0].amount -= ratio_quantity
            # ratio_quantity is expressed in % of total valuation

            order_tasks.append(
                self.execute_order(
                    quantity_quote_asset = total_valuation * ratio_quantity,
                    asset_to_decrease = position_to_decrease.asset,
                    asset_to_increase = position_to_increase.asset   
                )
            )
        return await self.gather(*order_tasks)

                
                
    
        
    