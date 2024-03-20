from decimal import Decimal
from datetime import datetime
from copy import deepcopy
from functools import lru_cache
from async_lru import alru_cache

from ..core import Pair, Quotation, Portfolio, Value
from ..simulations.simulation import AbstractPairSimulation
from ..time_managers import AbstractTimeManager

from .responses import OrderResponse, TickerResponse
from .exceptions import PairNotFound
from .exchange import AbstractExchange

class SimulationExchange(AbstractExchange):
    pair_symbol_separator = ""

    def __init__(self,
                 time_manager : AbstractTimeManager,
                 pair_simulations : dict[Pair, AbstractPairSimulation], 
                 initial_portfolio = Portfolio, 
                 trading_fees_pct = Decimal('0.001')# Binance fees 0.1%
        ):
        self.time_manager = time_manager
        self.pair_simulations = pair_simulations
        self.portfolio = initial_portfolio
        self.trading_fees_ratio = Decimal('1') - trading_fees_pct

        for pair_simulation in self.pair_simulations.values():
            self.time_manager.add_simulation(simulation= pair_simulation)

    async def get_available_pairs(self) -> list[Pair]: 
        return list(self.pair_simulations.keys())
    
    async def get_ticker_at_date(self, pair : Pair, date_close : datetime) -> TickerResponse:
        if pair not in self.pair_simulations :
            raise PairNotFound(pair= pair)
        data = self.pair_simulations[pair].get_data(date = date_close)
        return TickerResponse(
            status_code = 200,
            date_open= date_close - self.time_manager.interval,
            date_close= date_close,
            open = Quotation(Decimal(data["open"]), pair),
            high = Quotation(Decimal(data["high"]), pair),
            low = Quotation(Decimal(data["low"]), pair),
            close = Quotation(Decimal(data["close"]), pair),
            volume = Value(Decimal(data["volume"]), pair.asset),
            price = Quotation(Decimal(data["close"]), pair),
        )
    
    async def get_ticker(self, pair : Pair) -> TickerResponse:
        return await self.get_ticker_at_date(
            pair = pair,
            date_close = await self.time_manager.get_current_datetime()
        )
    
    async def get_portfolio(self) -> Portfolio:
        return deepcopy(self.portfolio)

    async def market_order(self, 
            pair : Pair, 
            quantity : Value
        ) -> OrderResponse:
        """Perform a order in the simulation

        Args:
            pair (Pair): Define the pair we want to trade on. E.g : BTCUSDT
            quantity (Value): The quantity desired for the trade. It can be expressed in both asset or quote asset of the pair with the following logic:
                Example on pair BTCUSDT with price P : 
                    - quantity = 5 BTC, means we want to buy 5 BTC. The simulation will compute the correct amoung of USDT
                     to sell (taking account fees) and perform the order. Math operations :     BTC(t+1) = BTC(t) + 5                       USDT(t+1) = USDT(t) - (5 * P) / (1 - fees)
                    - quantity = -5 BTC, means we want to sell 5 BTC. Math operations :         BTC(t+1) = BTC(t) - 5                       USDT(t+1) = USDT(t) + (5 * P) * (1 - fees)
                    - quantity = 100 USDT, means we want to buy 100 USDT. Math operations :     BTC(t+1) = BTC(t) - (100 / P) / (1 - fees)  USDT(t+1) = USDT(t) + 100 
                    - quantity = -100 USDT, means we want to sell 100 USDT. Math operations :   BTC(t+1) = BTC(t) + (100 / P) * (1 - fees)  USDT(t+1) = USDT(t) - 100

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        if quantity.asset == pair.quote_asset:
            return await self.market_order(pair = pair.reverse(), quantity= quantity)
        if quantity.asset != pair.asset:
            raise ValueError(f"quantity.quote_asset {quantity.asset} must match either pair.asset {pair.asset} or pair.quote_asset {pair.quote_asset}")
        
        # We made sur that quantity unit : asset
        price = await self.get_quotation(pair = pair) # unit : asset / quote_asset
    
        quantity_asset = quantity # unit : asset
        quantity_counterpart= quantity * price # unit : (asset) * (counterpart/ asset) = asset

        # Handle fees
        if quantity_asset.amount > Decimal('0') : # As we want to BUY, we need to sell more to equilibrate fees
            post_fees_quantity_counterpart= quantity_counterpart/ self.trading_fees_ratio
        else : # As we want to SELL, we need to buy less to equilibrate fees
            post_fees_quantity_counterpart= quantity_counterpart* self.trading_fees_ratio
        fees = abs(post_fees_quantity_counterpart- quantity_counterpart)

        self.portfolio = deepcopy(self.portfolio)

        self.portfolio.add_positions(
            positions = [
                quantity_asset,
                - post_fees_quantity_counterpart
            ],
        )
        return OrderResponse(
            status_code = 200,
            pair = pair,
            date = await self.time_manager.get_current_datetime(),
            original_quantity = quantity,
            counterpart_quantity = post_fees_quantity_counterpart,
            price = price,
            fees = fees
        )
