from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime as dt

import numpy as np
import pandas as pd


@dataclass
class DataBlock(ABC):
    """
    Object to store data for a given process and time period.
    """
    data_folder: str
    start_datetime: dt
    end_datetime: dt

    def load_data(self) -> pd.DataFrame:
        self._data = pd.DataFrame()
        return self._data

    @classmethod
    def slice(cls, start_datetime: dt, end_datetime: dt) -> DataBlock:
        """
        Returns a DataBlock object sliced from the given start and end time.
        """
        new_block = DataBlock(
            cls.data_folder, start_datetime, end_datetime
            )
        drop_rows = pd.concat([
                cls._data[cls._data.index < start_datetime],
                cls._data[cls._data.index > end_datetime]
            ]).index

        new_block._data = cls._data.drop(drop_rows)

        ## IMPLEMENT CHECKS FOR TIME VALIDITY
        if new_block._data.index is not None:
            return new_block
        else:
            raise Exception("No data exists in slice.")

    def split(self, freq: str ='h') -> list:
        """
        Splits the DataBlock into multiple smaller objects
        at the specified datetime frequency (default hourly).
        """
        blocks = []
        datetimes = pd.date_range(
            self.start_datetime, self.end_datetime, freq=freq
            ).to_pydatetime()
        time_delta = pd.Timedelta(1, freq)

        for start_datetime in np.delete(datetimes, -1):
            end_datetime = start_datetime + time_delta
            blocks.append(DataBlock.slice(self, start_datetime, end_datetime))
        
        return blocks

    def data(self) -> pd.DataFrame:
        """
        Returns all cycles stored for the DataBlock.
        """
        try:
            return self._data
        except AttributeError:
            pass

    def first_cycle(self) -> pd.DatetimeIndex:
        """
        Returns time of first cycle for the given data.
        """
        try:
            return self._first_cycle
        except AttributeError:
            self._first_cycle = min(self.data().index)
            return self._first_cycle

    def last_cycle(self) -> pd.DatetimeIndex:
        """
        Returns time of last cycle for the given data.
        """
        try:
            return self._last_cycle
        except AttributeError:
            self._last_cycle = max(self.data().index)
            return self._last_cycle

    def total_time(self) -> float:
        """
        Returns the time difference (in seconds)
        between the first and last cycle.
        """
        try:
            return self._total_time
        except AttributeError:
            self._total_time = (
                self.last_cycle() - self.first_cycle()
                ).total_seconds()
            return self._total_time

    def cycle_times(self) -> pd.Series:
        """
        Returns cycle times for the data.
        """
        try:
            return self._cycle_times
        except AttributeError:
            self.data()['cycle_time'] = self.data()['timestamp'].diff()
            self._cycle_times = self.data()['cycle_time']
            return self._cycle_times

    def cycle_rates(self) -> pd.Series:
        """
        Returns instantaneous cycle rates for the data.
        """
        try:
            return self._cycle_rates
        except AttributeError:
            self.data()['cycle_rate'] = 60 / self.data()['cycle_time']
            self._cycle_rates = self.data()['cycle_rate']
            return self._cycle_rates

    def cycle_count(self) -> int:
        """
        Returns a cycle count for the given data.
        """
        try:
            return self._cycle_count
        except AttributeError:
            self._cycle_count = len(self.data().index)
            return self._cycle_count

    ## OTHER METHODS TO MANIPULATE AND VISUALIZE DATA