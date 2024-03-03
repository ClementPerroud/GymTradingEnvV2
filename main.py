from decimal import Decimal
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from environment import TradingEnv
from time_managers import SimulationTimeManager
from simulations import RandomPairSimulation, HistoricalSimulation
from exchanges import SimulationExchange
from actions import DiscreteActionManager, DiscreteExpositionAction, DiscreteDoNothing
from observers import TickerObserver
from rewards import PerformanceReward
from enders import ValuationEnder
from core import Portfolio, Asset, Value, Pair


async def main():
    BTC = Asset("BTC")
    ETH = Asset("ETH")
    USDT = Asset("USDT")
    BTCUSDT = Pair(BTC, USDT)
    ETHUSDT = Pair(ETH, USDT)
    quote_asset = USDT

    df = pd.read_csv("BTC-USDT.csv")
    df["date_open"] = pd.to_datetime(df["open_time"], format= "ISO8601")
    df["date_close"] = df["date_open"] + timedelta(minutes=1)
    df.set_index("date_close", inplace= True)
    df = df.resample(timedelta(minutes=1)).ffill()


    time_manager = SimulationTimeManager(interval= timedelta(hours=1))

    exchange = SimulationExchange(
        time_manager= time_manager,
        pair_simulations={
            BTCUSDT : HistoricalSimulation(dataframe= df),
            ETHUSDT : RandomPairSimulation(
                initial_price_amount= 10_000, year_return= 0, year_std= 0
            )
        },
        initial_portfolio= Portfolio(
            name = "Main",
            positions= [
                Value(amount = Decimal("1000"), asset= USDT)
            ]
        ),
        trading_fees_pct = Decimal('0.2') / Decimal('100')
    )

    action_manager = DiscreteActionManager(
        actions = [
            await DiscreteExpositionAction.create(
                target_exposition= {
                    BTC : Decimal("1"),
                },exchange= exchange, quote_asset= quote_asset
            ),
            await DiscreteExpositionAction.create(
                target_exposition= {
                    USDT : Decimal("1")
                },exchange= exchange, quote_asset= quote_asset
            ),
            await DiscreteExpositionAction.create(
                target_exposition= {
                    ETH : Decimal("1")
                }, exchange= exchange, quote_asset= quote_asset
            ),
            await DiscreteExpositionAction.create(
                target_exposition= {
                    BTC : Decimal("0.33"), ETH : Decimal("0.33"), USDT : Decimal("0.34")
                }, exchange= exchange, quote_asset= quote_asset
            ),
            DiscreteDoNothing()
        ]
    )
    observer = TickerObserver(pair = BTCUSDT, exchange= exchange, time_manager= time_manager)
    reward = await PerformanceReward.create(exchange= exchange, quote_asset= quote_asset)

    trading_environment = TradingEnv(
        time_manager= time_manager,
        action_manager= action_manager,
        observer= observer,
        reward= reward,
        enders= [
            await ValuationEnder.create(valuation_threeshold=Value(amount = Decimal("10"), asset= USDT), exchange= exchange)
        ]
    )

    date = datetime(2018, 1, 1)
    obs, infos = await trading_environment.reset(date = date)
    terminated, truncated = False, False
    step = 0

    import time
    start = time.time()
    while not truncated and not terminated:
        action = action_manager.action_space().sample()
        obs, reward, terminated, truncated, infos = await trading_environment.step(action= action)
        step += 1

    end = time.time()
    print(f"{step} step in {end - start :0.2f} seconds : {(end-start) / step * 1000 : 0.2f} s / 1 000 steps")


if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()

    # Side note: Apparently, async() will be deprecated in 3.4.4.
    # See: https://docs.python.org/3.4/library/asyncio-task.html#asyncio.async
    tasks = asyncio.gather(
        main()
    )
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        print("Caught keyboard interrupt. Canceling task...")
        import sys
        sys.exit()
    finally:
        loop.close()