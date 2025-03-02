
import pandas as pd
import numpy as np
import pytz
from datetime import datetime
from functools import partial
from warnings import warn
from typing import Dict, Tuple, Union

from .simulation import AbstractPairSimulation
from ..checkers import AbstractChecker
from ..core.pair import Pair


class HistoricalSimulation(AbstractPairSimulation, AbstractChecker):
    def __init__(self,
            pair : Pair,
            date_close_name = "date_close",
            date_open_name = "date_open",
            open_name = "open",
            high_name = "high",
            low_name = "low",
            close_name = "close",
            volume_name = "volume",
            other_aggregation : Dict[str, object]= {},
            on_missing_date = "error"
            ) -> None:
        
        super().__init__()
        self.pair = pair
        (self.date_close_name, self.date_open_name, self.open_name, 
         self.high_name, self.low_name, self.close_name, self.volume_name) = (
            date_close_name, date_open_name, open_name, 
            high_name, low_name, close_name, volume_name 
         )
        self.other_aggregation = other_aggregation

        # Preparing aggreation
        # Named based aggregation
        temp_base_aggregation = {
            "open" : lambda x : x[0],
            "high": lambda x : x.max(),
            "low" : lambda x : x.min(),
            "close" : lambda x: x[-1],
            "volume": lambda x: x.sum()
        }
        self.name_aggreation = {**other_aggregation,  **temp_base_aggregation}

        if on_missing_date not in ["error", "warn", None]:
            raise ValueError("on_missing_date must be in ['error', 'warn', None].")
        self.on_missing_date = on_missing_date


    def set_df(self, 
            dataframe : pd.DataFrame,
        ):
        self.dataframe = dataframe.reset_index(drop=False)
        self.dataframe.rename(
            columns = {
                self.date_open_name : "date_open",
                self.date_close_name : "date_close",
                self.open_name : "open",
                self.high_name : "high",
                self.low_name : "low",
                self.close_name : "close",
                self.volume_name : "volume"
            },
            inplace= True
        )
        self.main_interval = self.dataframe["date_close"].diff().value_counts().index[0]
        self.dataframe.set_index("date_close", inplace= True)
        self.dataframe.sort_index(inplace= True)
        self.dates = self.dataframe.index.to_numpy()
        self.data_array = self.dataframe.to_numpy()
        self.data_array_len = len(self.data_array)

        # Check if columns from other_aggregation exist
        for col in self.other_aggregation.keys():
            if col not in self.dataframe.columns:
                raise KeyError(f"Column name {col} from other_aggregation does not exist.")
        
        # Automatic column selection for the aggreation
        self.aggregation = {}
        func = lambda array, i, col : self.name_aggreation[col](array[:, i])
        for i, col in enumerate(self.dataframe.columns):
            if col in self.name_aggreation:
                self.aggregation[col] = partial(func, i = i, col = col)

    async def reset(self, seed = None) -> None:
        self.time_manager = self.get_trading_env().time_manager
        date = await self.time_manager.get_current_datetime()
        np_date = np.datetime64(date.astimezone(pytz.UTC).replace(tzinfo = None))
        if np_date >= self.dates[-1] or np_date <= self.dates[0]: raise ValueError(f"This date {date} is not valid. Please select a date between {self.dates[0]} and {self.dates[-1]}")

        self.past_index = np.searchsorted(self.dates, np_date, side="left")
        self.past_date = date
        await super().reset(seed = seed)
        
    def __aggregrate(self, array: np.ndarray):
        return {col : agg(array) for col, agg in self.aggregation.items()}

        
    async def forward(self, date : datetime) -> None:
        np_date = np.datetime64(date.astimezone(pytz.UTC).replace(tzinfo = None))
        await super().forward(date= date)

        index = np.searchsorted(self.dates, np_date, side="right")-1

        self.trainable = True
        if np_date != self.dates[index]: 
            message = f'No row found for date : {date}.'
            self.trainable = False
            if self.on_missing_date == "warn" : warn(message= message)
            elif self.on_missing_date == "error" : ValueError(message)
        
        real_index_gap = index - self.past_index
        if real_index_gap > 0:
            array = self.data_array[self.past_index + 1:index + 1]
        else:
            array = self.data_array[index: index+1]
        # if real_index_gap <= 0: 
        #     raise ValueError(f"""
        #         Could not find any data to aggregate between {self.past_date} and {date}.
        #         Please increase you interval or increase the granularity of the dataframe. """)


        data = self.__aggregrate(array=array)
        theoritical_index_gap = (date - self.past_date)/self.main_interval
        self.last_trainable = True
        if real_index_gap < theoritical_index_gap * 0.8 :
            self.last_trainable= False



        self.update_memory(date=date, data=data)

        self.last_index_gap = real_index_gap
        self.past_index = index
        self.past_date = date


    async def check(self) -> Tuple[bool, bool]:
        return (
            False, 
            (self.past_index + self.last_index_gap + 1) >= self.data_array_len,
            self.last_trainable
        )

        