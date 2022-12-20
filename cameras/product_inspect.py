from dataclasses import dataclass
from datetime import datetime as dt

import pandas as pd

from cameras import Camera
from datafiles import DataBlock


class ProductInspectCamera(Camera):
    """
    Poucher Product Inspect Camera (iTrak Poucher)
    """

    PROCESS_CODE = 'PR'
    MAX_CYCLE_TIME = 1.2


    def __init__(self, machine_info: dict) -> None:
        self.machine_info = machine_info
        self.data_folder = self.machine_info.get('data_folder')

    def load_data(self, start_datetime: dt, end_datetime: dt) -> DataBlock:
        """
        Returns a DataBlock object of process data for the given timespan.
        """
        return DataBlock(
            self.data_folder, ProductInspectCamera.PROCESS_CODE,
            start_datetime, end_datetime
            )

    @staticmethod
    def parts(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns all cycles with a part present.
        """
        return data[data['part_present'] == 1]

    @staticmethod
    def cumulative_parts(data: pd.DataFrame) -> pd.Series:
        """
        Returns a column of cumulative parts for the data.
        """
        return data['part_present'].cumsum()

    @staticmethod
    def empty_cycles(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns all cycles with no part present.
        """
        return data[data['part_present'] == 0]

    @staticmethod
    def reworks(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns all cycles with duplicate serial numbers.
        """
        return data[data.duplicated('serial_number')]

    @staticmethod
    def first_part(data: pd.DataFrame) -> pd.DatetimeIndex:
        """
        Returns time of first part made.
        """
        return min(data[data['part_present'] == 1].index)

    @staticmethod
    def last_part(data: pd.DataFrame) -> pd.DatetimeIndex:
        """
        Returns time of last part made.
        """
        return max(data[data['part_present'] == 1].index)

    @staticmethod
    def stops(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns all cycles which exceed maximum cycle time.
        """
        return data[
            data['cycle_time'] > ProductInspectCamera.MAX_CYCLE_TIME
            ]