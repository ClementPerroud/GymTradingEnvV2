from decimal import Decimal
import asyncio

from .action import AbstractAction
from managers.analyser import PortfolioManager
from exchanges import AbstractExchange
from core import Asset, Pair, Value, PortfolioExposition
from managers.exchange import ExchangeManager

class DiscreteExpositionAction(AbstractAction):
    def __init__(self, target_exposition : dict[Asset, Decimal], exchange : AbstractExchange, quote_asset : Asset):
        self.target_exposition = PortfolioExposition(
                expositions= target_exposition
            )
        self.exchange = exchange
        self.portfolio_manager = PortfolioManager(
            exchange= exchange,
            quote_asset = quote_asset
        )
        self.order_manager = ExchangeManager(exchange= self.exchange)

    async def execute_order(self, asset_to_decrease : Asset, asset_to_increase : Asset, quantity_quote_asset : Value):
        quote_asset = quantity_quote_asset.asset
        if asset_to_decrease == quote_asset:
                quantity_asset = - quantity_quote_asset
        else:
            quantity_asset = - quantity_quote_asset * (await self.exchange.get_quotation(pair = Pair(asset_to_decrease, quote_asset= quote_asset))).reverse()

        pair = Pair(asset= asset_to_increase, quote_asset= asset_to_decrease)
        await self.order_manager.market_order(
            quantity= quantity_asset,
            pair = pair
        )

    async def execute(self):
        current_position = await self.exchange.get_portfolio()
        async with asyncio.TaskGroup() as tg:
            total_valuation_task = tg.create_task(self.portfolio_manager.valuation(
                portfolio= current_position
            ))
            current_exposition_task = tg.create_task(self.portfolio_manager.exposition(
                portfolio= current_position
            ))
        total_valuation : Value = total_valuation_task.result()
        quote_asset = total_valuation.asset

        current_exposition = current_exposition_task.result()

        diff_exposition = self.target_exposition - current_exposition
        diff_positions_percent = diff_exposition.get_positions()

        # Prepare
        list_position_to_increase : list[Value] = [] # Position to gincrease
        list_position_to_decrease : list[Value] = [] # Position to decrease
        for position in diff_positions_percent:
            if position.amount > 0: list_position_to_increase.append(position)
            else: list_position_to_decrease.append( - position) # We make them positive

        # Compute how to re equilibrate porfolio
        async with asyncio.TaskGroup() as tg:
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
                    tg.create_task(
                        self.execute_order(
                            quantity_quote_asset = total_valuation * ratio_quantity,
                            asset_to_decrease = position_to_decrease.asset,
                            asset_to_increase = position_to_increase.asset   
                        )
                    )
                )

                
                
    
        
    