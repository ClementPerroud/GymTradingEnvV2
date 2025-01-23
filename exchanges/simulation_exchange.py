from decimal import Decimal
from datetime import datetime, timedelta
from copy import deepcopy
from typing import List, Dict

from ..core import Asset, Pair, Quotation, Portfolio, Value
from ..simulations.simulation import AbstractPairSimulation
from ..time_managers import AbstractTimeManager
from ..utils.async_lru import alru_cache
from ..utils.speed_analyser import astep_timer

from .responses import OrderResponse, TickerResponse
from .exceptions import PairNotFound
from .exchange import AbstractExchange

class SimulationExchange(AbstractExchange):
    pair_symbol_separator = ""

    def __init__(self,
                 initial_portfolio : Portfolio, 
                 pair_simulations : Dict[Pair, AbstractPairSimulation], 
                 trading_fees_pct = Decimal('0.001'),# Binance fees 0.1%
                 asset_yearly_borrowing_interest : Dict[Asset, Decimal] = {}
        ):
        self.pair_simulations = pair_simulations
        self.initial_portfolio = initial_portfolio
        self.asset_yearly_borrowing_interest = asset_yearly_borrowing_interest
        self.trading_fees_ratio = Decimal('1') - trading_fees_pct

    async def reset(self, seed = None):
        self.portfolio = deepcopy(self.initial_portfolio)
        self.time_manager : AbstractTimeManager = self.get_trading_env().time_manager

    async def forward(self, date: datetime, seed=None):
        await super().forward(date, seed)
        elapsed_time = (await self.time_manager.get_historical_datetime(step_back=1) - date)
        ratio = Decimal.from_float(elapsed_time / timedelta(days = 365.25))
        portfolio = await self.get_portfolio()

        for asset, yearly_borrowing_fee in self.asset_yearly_borrowing_interest.items():
            position = portfolio.get_position(asset= asset)
            if position is not None and position.amount <  Decimal('0'):
                self.portfolio.add_position(
                    Value(
                        amount = - abs(position.amount) * yearly_borrowing_fee * ratio,
                        asset=asset
                    )
                )
        
    async def get_available_pairs(self) -> List[Pair]: 
        return list(self.pair_simulations.keys())
    
    @astep_timer("Get Ticker", level= 2)
    @alru_cache(maxsize= 1_000)
    async def get_ticker(self, pair : Pair, date : datetime) -> TickerResponse:
        if pair not in self.pair_simulations : raise PairNotFound(pair= pair)
        if date is None:date = await self.time_manager.get_current_datetime()

        data = self.pair_simulations[pair].get_data(date = date)
        return TickerResponse(
            status_code = 200,
            date_open= await self.time_manager.get_historical_datetime(step_back=1, relative_date= date),
            date_close= date,
            open = Quotation(Decimal(data["open"]), pair),
            high = Quotation(Decimal(data["high"]), pair),
            low = Quotation(Decimal(data["low"]), pair),
            close = Quotation(Decimal(data["close"]), pair),
            volume = Value(Decimal(data["volume"]), pair.asset),
            price = Quotation(Decimal(data["close"]), pair),
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
