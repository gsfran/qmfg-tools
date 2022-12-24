from abc import ABC, abstractmethod
from datetime import datetime as dt

import pandas as pd

from datafiles import DataBlock


class Camera(ABC):
    """
    Machine vision system camera object. Any model capable of datalogging to /Process_Data/.
    """

    @abstractmethod
    def load_data(self, start_datetime: dt, end_datetime: dt) -> DataBlock:
        pass

    @staticmethod
    def analyze_cycles(data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates cycle times and instantaneous run rates for data cycles.
        """
        data['cycle_times'] = Camera.cycle_times(data)
        data['cycle_rates'] = Camera.cycle_rates(data)
        return data

    @staticmethod
    def cycle_times(data: pd.DataFrame) -> pd.Series:
        """
        Returns cycle times for the given data.
        """
        return data['timestamp'].diff()

    @staticmethod
    def cycle_rates(data: pd.DataFrame) -> pd.Series:
        """
        Returns instantaneous machine speeds for the given data. [upm]
        """
        return 60 / data['cycle_time']

    @staticmethod
    def first_cycle(data: pd.DataFrame) -> pd.DatetimeIndex:
        """
        Returns time of first cycle for the given data.
        """
        return min(data.index)

    @staticmethod
    def last_cycle(data: pd.DataFrame) -> pd.DatetimeIndex:
        """
        Returns time of last cycle for the given data.
        """
        return max(data.index)