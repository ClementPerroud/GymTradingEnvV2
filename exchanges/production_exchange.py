from decimal import Decimal, ROUND_FLOOR
from datetime import datetime
import pandas as pd
import numpy as np
import pytz
from typing import List
from binance import AsyncClient

from ..core import Asset, Pair, Quotation, Portfolio, Value

from .responses import OrderResponse, TickerResponse
from .exchange import AbstractExchange

class BinanceProductionExchange(AbstractExchange):
    def __init__(self, api_key : str, api_secret : str, testnet = False, kline_interval = AsyncClient.KLINE_INTERVAL_1MINUTE) -> None:
        super().__init__()
        self.client = None
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.kline_interval = kline_interval

    async def reset(self, seed = None) -> None:
        await super().reset(seed = seed)
        if self.client is None:
            self.client = await AsyncClient.create(self.api_key, self.api_secret, testnet= self.testnet)
        
        self.time_manager = self.get_trading_env().time_manager
    
    async def get_info(self):
        info = await self.client.get_exchange_info()
        self.__symbol_infos = {}
        for symbol_info in info["symbols"]:
            self.__symbol_infos[symbol_info["symbol"]] = symbol_info
        return info
    
    async def get_pair_info(self, pair : Pair):
        await self.get_info()
        return self.__symbol_infos[pair.__repr__(separator="")]

    async def get_available_pairs(self) -> List[Pair]:
        info = await self.get_info()
        symbols_info = info["symbols"]

        # Retrieve all assets
        assets = [d["baseAsset"] for d in symbols_info] + [d["quoteAsset"] for d in symbols_info]
        assets = list(dict.fromkeys(assets))
        assets = {name : Asset(name = name) for name in assets}

        # Retrieve all pairs
        pairs = [Pair(asset= assets[d["baseAsset"]], quote_asset=assets[d["quoteAsset"]]) for d in symbols_info]
        return pairs

    async def get_ticker(self, pair : Pair, date : datetime = None) -> TickerResponse:
        if date is None: date = await self.time_manager.get_current_datetime()

        open_date = await self.time_manager.get_historical_datetime(step_back=1,relative_date= date)

        klines = await self.client.get_historical_klines(
            symbol = pair.__repr__(separator= ""),
            interval = '1m',
            end_str= str(int(date.timestamp() * 1E6) - 1),
            start_str= str(int(open_date.timestamp() * 1E6)),
        )

        klines = [kline[0:7] for kline in klines]
        klines = pd.DataFrame(klines, columns= ["date_open", "open", "high", "low", "close", "volume", "date_close"])
        klines["date_open"] = pd.to_datetime(klines["date_open"], unit = "ms", utc = True)
        klines["date_close"] = pd.to_datetime(klines["date_close"], unit = "ms", utc = True)
        klines.sort_values(by="date_close", ascending= True, inplace= True)
        # Convert to Decimal
        klines[["open", "high", "low", "close", "volume"]] = \
            klines[["open", "high", "low", "close", "volume"]].map(lambda cell : Decimal(cell))

        return TickerResponse(
            status_code= 200,
            date_open=open_date,
            date_close= date,
            open = Quotation(klines["open"].iloc[0], pair),
            high = Quotation(klines["high"].max(), pair),
            low = Quotation(klines["low"].min(), pair),
            close = Quotation(klines["close"].iloc[-1], pair),
            volume = Value(klines["volume"].sum(), pair.asset),
            price= Quotation(klines["close"].iloc[-1], pair)
        )
    
    async def get_portfolio(self) -> Portfolio:
        margin_account = await self.client.get_margin_account(recvWindow = 10000)
        user_assets_info = margin_account["userAssets"]
        positions = []
        for asset_info in user_assets_info:
            amount = Decimal(asset_info["free"]) - Decimal(asset_info["borrowed"]) - Decimal(asset_info["interest"])
            if amount > 0:
                positions.append(Value(
                    amount = amount,
                    asset= Asset(name = asset_info["asset"])
                ))
        return Portfolio(positions= positions)

    async def market_order(self, quantity : Value, pair : Pair) -> OrderResponse:
        try:
            info = await self.get_pair_info(pair=pair)
        except KeyError as e:
            pair = pair.reverse()
            info = await self.get_pair_info(pair= pair)
        for _filter in info["filters"]:
            if _filter["filterType"] == "LOT_SIZE":
                base_asset_precision = Decimal(_filter["stepSize"]).normalize() # Normalize helps get rid of the excess zeros
                break
        
        quantity.amount = quantity.amount.quantize(base_asset_precision, rounding= ROUND_FLOOR)
        # Example on pair BTCUSDT
        if quantity.amount == 0: return

        # E.g : quantity = 1.2 BTC
        if quantity.asset == pair.asset:
            quantity_base_asset = abs(quantity.amount)
            quantity_quote_asset = None
            side = AsyncClient.SIDE_BUY if quantity.amount > 0 else AsyncClient.SIDE_SELL
        # E.g : quantity = -156 USDT
        elif quantity.asset == pair.quote_asset:
            quantity_base_asset = None
            quantity_quote_asset = abs(quantity.amount)
            side = AsyncClient.SIDE_SELL if quantity.amount > 0 else AsyncClient.SIDE_BUY


        params = dict(symbol = pair.__repr__(separator=""),
            isIsolated = "FALSE",
            side = side,
            type = AsyncClient.ORDER_TYPE_MARKET,
            sideEffectType = "AUTO_BORROW_REPAY",
            recvWindow = 10000
        )
        if quantity_base_asset is not None: params["quantity"] = quantity_base_asset
        if quantity_quote_asset is not None: params["quoteOrderQty"] = quantity_quote_asset

        print(params)
        order_response = await self.client.create_margin_order(**params)

        counterpart_quantity = Value(order_response["cummulativeQuoteQty"], pair.quote_asset)
        
        average_price = Decimal('0')
        sum_qty = Decimal('0')
        sum_fees = None
        for fill in order_response["fills"]:
            average_price += Decimal(fill["price"]) * Decimal(fill["qty"])
            sum_qty += Decimal(fill["qty"])
            sum_fees = Value(fill["commission"], Asset(fill["commissionAsset"])) + sum_fees
        average_price /= sum_qty

        return OrderResponse(
            status_code= 200,
            pair= pair,
            date= datetime.now(tz=pytz.UTC),
            original_quantity= quantity,
            counterpart_quantity= None,
            price= average_price,
            fees = sum_fees
        )
