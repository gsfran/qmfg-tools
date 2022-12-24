# from __future__ import annotations

from datetime import datetime as dt

import pandas as pd

from cameras import Camera
from datafiles import *


class ProductInspect(Camera):
    """
    iTrak Poucher Product Inspect Camera object.
    """

    PROCESS_CODE = 'PR'
    MAX_CYCLE_TIME = 1.2

    RAW_DATA_HEADERS = [
        "item_number", "lot_number", "serial_number",
        "part_present", "cognex_timestamp"
        ]

    def __init__(self, machine_info: dict) -> None:
        self.machine_info = machine_info
        self.data_folder = self.machine_info.get('data_folder')

    def load_data(self, start_datetime: dt, end_datetime: dt) -> DataBlock:
        """
        Returns a DataBlock object of process data for the given timespan.
        """
        return DataBlock(
            self.data_folder, ProductInspect.PROCESS_CODE,
            start_datetime, end_datetime
        )


    # region run_stats

    @staticmethod
    def run_stats(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns run statistics for the given data.
        """

        RUN_STATS_DICT = {
            'total_cycles': ProductInspect.cycle_count,
            'parts_pouched': ProductInspect.part_count,
            'production_time': ProductInspect.production_time,
            'first_part_pouched': ProductInspect.first_part,
            'last_part_pouched': ProductInspect.last_part,
            'empty_count': ProductInspect.empty_count,
            'empty_rate': ProductInspect.empty_rate,
            'rework_count': ProductInspect.rework_count,
            'rework_rate': ProductInspect.rework_rate
        }

        run_stats = pd.DataFrame(columns=RUN_STATS_DICT.keys())

        for stat, method in RUN_STATS_DICT.items():
            run_stats[stat] = method(data)

        return run_stats

    @staticmethod
    def cycle_count(data: pd.DataFrame) -> int:
        """
        Returns a cycle count for the given data.
        """
        return len(data)

    @staticmethod
    def part_cycles(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns non-empty poucher cycles for the given data.
        """
        return data[data['part_present'] == 1]
        
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
    def production_time(data: pd.DataFrame) -> float:
        """
        Returns the time difference of the first and last part.
        """
        return (
            ProductInspect.last_part(data)
            - ProductInspect.first_part(data)
            )

    @staticmethod
    def part_count(data: pd.DataFrame) -> int:
        """
        Returns the number of non-empty cycles for the given data.
        """
        return len(ProductInspect.part_cycles(data))

    @staticmethod
    def cumulative_part_count(data: pd.DataFrame) -> pd.Series:
        """
        Returns a column of cumulative parts for the given data.
        """
        return data['part_present'].cumsum()

    @staticmethod
    def empty_cycles(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns all cycles with no part present.
        """
        return data[data['part_present'] == 0]

    @staticmethod
    def empty_count(data: pd.DataFrame) -> int:
        """
        Returns the number of empty cycles for the given data.
        """
        return len(ProductInspect.empty_cycles(data))

    @staticmethod
    def empty_rate(data: pd.DataFrame) -> float:
        """
        Returns the decimal percentage of empty cycles for the data.
        """
        return (
            ProductInspect.empty_count(data)
            / ProductInspect.cycle_count(data)
        )

    @staticmethod
    def reworks(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns all cycles with duplicate serial numbers.
        """
        return data[data.duplicated('serial_number')]

    @staticmethod
    def rework_count(data: pd.DataFrame) -> int:
        """
        Returns the number of parts reworked.
        """
        return len(ProductInspect.reworks(data))

    @staticmethod
    def rework_rate(data: pd.DataFrame) -> float:
        """
        Returns the decimal percentage of reworked parts.
        """
        return (
            ProductInspect.rework_count(data)
            / ProductInspect.cycle_count(data)
        )

    # endregion

    #region stop_stats

    @staticmethod
    def stop_stats(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns stop statistics for the given data.
        """

        STOP_STATS_DICT = {
            'total_run_time': 1,
            'net_run_time': 1,
            'total_run_perc': 1,
            'total_stop_time': 1,
            'total_stop_perc': 1,
            'short_stop_time': 1,
            'medium_stop_time': 1,
            'long_stop_time': 1,
            'extra_long_stop_time': 1,
            'short_stop_%': 1,
            'medium_stop_%': 1,
            'long_stop_%': 1,
            'extra_long_stop_%': 1
        }

    @staticmethod
    def stops(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns all cycles which exceed maximum cycle time.
        """
        return data[data['cycle_time'] > ProductInspect.MAX_CYCLE_TIME]

    @staticmethod
    def total_stop_time(data: pd.DataFrame) -> float:
        """
        Returns the sum of cycle times greater than the maximum.
        """
        return sum(ProductInspect.stops(data).loc['cycle_time'])

    @staticmethod
    def total_run_time(data: pd.DataFrame) -> float:
        """
        Returns the sum of cycle times less than the maximum.
        """
        return (
            ProductInspect.run_stats(data).loc['production_time']
            - ProductInspect.stops(data).loc['cycle_time']
            )
    #endregion