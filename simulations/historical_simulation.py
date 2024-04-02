
import pandas as pd
import numpy as np
from datetime import datetime
from functools import partial
from warnings import warn
from typing import Dict, Tuple, Union

from .simulation import AbstractPairSimulation
from ..enders import AbstractEnder



class HistoricalSimulation(AbstractPairSimulation, AbstractEnder):
    def __init__(self,
            dataframe : pd.DataFrame,
            date_close = "date_close",
            date_open = "date_open",
            open_name = "open",
            high_name = "high",
            low_name = "low",
            close_name = "close",
            volume_name = "volume",
            other_aggregation : Dict[str, object]= {},
            on_missing_date = "error"
            ) -> None:
        
        super().__init__()
        self.dataframe = dataframe.reset_index(drop=False)
        self.dataframe.rename(
            columns = dict(zip(
                [date_open, date_close, open_name, high_name, low_name, close_name, volume_name],
                ["date_open", "date_close", "open", "high", "low", "close", "volume"]
            )),
            inplace= True
        )
        self.main_interval = self.dataframe["date_close"].diff().value_counts().index[0]
        self.dataframe.set_index("date_close", inplace= True)
        self.dataframe.sort_index(inplace= True)
        self.dates = self.dataframe.index.to_numpy()
        self.data_array = self.dataframe.to_numpy()
        self.data_array_len = len(self.data_array)

        # Preparing aggreation
        # Named based aggregation
        temp_base_aggregation = {
            "open" : lambda x : x[0],
            "high": lambda x : x.max(),
            "low" : lambda x : x.min(),
            "close" : lambda x: x[-1],
            "volume": lambda x: x.sum()
        }
        # Check if columns from other_aggregation exist
        for col in other_aggregation.keys():
            if col not in self.dataframe.columns:
                raise KeyError(f"Column name {col} from other_aggregation does not exist.")
        
        self.name_aggreation = {**other_aggregation,  **temp_base_aggregation}
        # Automatic column selection for the aggreation
        self.aggregation = {}
        func = lambda array, i, col : self.name_aggreation[col](array[:, i])
        for i, col in enumerate(self.dataframe.columns):
            if col in self.name_aggreation:
                self.aggregation[col] = partial(func, i = i, col = col)

        if on_missing_date not in ["error", "warn", None]:
            raise ValueError("on_missing_date must be in ['error', 'warn', None].")
        self.on_missing_date = on_missing_date

    async def reset(self, date : datetime, seed = None) -> None:
        np_date = np.datetime64(date)
        if np_date >= self.dates[-1] or np_date <= self.dates[0]: raise ValueError(f"This date {date} is not valid. Please select a date between {self.dates[0]} and {self.dates[-1]}")

        self.past_index = np.searchsorted(self.dates, np_date, side="left")
        self.past_date = date
        await super().reset(date= date, seed = seed)
        
    def __aggregrate(self, array: np.ndarray):
        return {col : agg(array) for col, agg in self.aggregation.items()}

        
    async def forward(self, date : datetime) -> None:
        np_date = np.datetime64(date)
        await super().forward(date= date)

        index = np.searchsorted(self.dates, np_date, side="right")-1

        self.trainable = True
        if np_date != self.dates[index]: 
            message = f'No row found for date : {date}.'
            self.trainable = False
            if self.on_missing_date == "warn" : warn(message= message)
            elif self.on_missing_date == "error" : ValueError(message)
        
        index_gap = index - self.past_index
        if index_gap > 0:
            array = self.data_array[self.past_index + 1:index + 1]
        else:
            array = self.data_array[index: index+1]
        # if index_gap <= 0: 
        #     raise ValueError(f"""
        #         Could not find any data to aggregate between {self.past_date} and {date}.
        #         Please increase you interval or increase the granularity of the dataframe. """)


        data = self.__aggregrate(array=array)
        if (date - self.past_date)/self.main_interval * 0.8 > index_gap:
            self.trainable = False 



        self.update_memory(date=date, data=data)

        self.last_index_gap = index_gap
        self.past_index = index
        self.past_date = date


    async def check(self) -> Tuple[bool, bool]:
        return (
            False, 
            (self.past_index + self.last_index_gap + 1) >= self.data_array_len, 
            self.trainable
        )

        