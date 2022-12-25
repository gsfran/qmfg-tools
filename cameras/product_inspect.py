from datetime import datetime as dt

import pandas as pd

from cameras import Camera
from datafiles import *


class ProductInspect(Camera):
    """
    iTrak Poucher Product Inspect Camera object.
    """

    PROCESS_CODE = 'PR'
    IDEAL_RUN_RATE = 140
    MAX_CYCLE_TIME = 1.2

    OEE_STOP_CUTOFF = 120
    SHORT_STOP_BIN_WIDTH = 2
    LONG_STOP_BIN_WIDTH = 60

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
            self.data_folder,
            ProductInspect.PROCESS_CODE, ProductInspect.RAW_DATA_HEADERS,
            start_datetime, end_datetime
        )

    # region stats
    @staticmethod
    def stats(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns all statistics for the given data.
        """
        return pd.concat(
            [
                ProductInspect.run_stats(data),
                ProductInspect.stop_stats(data),
                ProductInspect.oee_stats(data)
            ], axis=1
        )

    @staticmethod
    def run_stats(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns run statistics for the given data.
        """

        RUN_STATS_DICT = {
            'total_cycles': ProductInspect.cycle_count,
            'total_time': ProductInspect.total_time,

            'parts_pouched': ProductInspect.part_count,
            'first_part_pouched': ProductInspect.first_part,
            'last_part_pouched': ProductInspect.last_part,
            'production_time': ProductInspect.production_time,

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
    def stop_stats(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns stop statistics for the given data.
        """

        STOP_STATS_DICT = {
            'total_stop_count': ProductInspect.total_stop_count,
            'total_stop_time': ProductInspect.total_stop_time,
            'total_run_time': ProductInspect.total_run_time,

            'short_stop_count': ProductInspect.short_stop_count,
            'short_stop_time': ProductInspect.short_stop_time,

            'long_stop_count': ProductInspect.long_stop_count,
            'long_stop_time': ProductInspect.long_stop_time,
        }

        stop_stats = pd.DataFrame(columns=STOP_STATS_DICT.keys())

        for stat, method in STOP_STATS_DICT.items():
            stop_stats[stat] = method(data)

        return stop_stats
    
    @staticmethod
    def oee_stats(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns OEE statistics for the given data.
        """

        OEE_STATS_DICT = {
            'oee_run_time': ProductInspect.oee_run_time,

            'availability_rate': ProductInspect.availability_rate,
            'performance_rate': ProductInspect.performance_rate,
            'quality_rate': ProductInspect.quality_rate,

            'oee_rate': ProductInspect.oee_rate
        }

        oee_stats = pd.DataFrame(columns=OEE_STATS_DICT.keys())

        for stat, method in OEE_STATS_DICT.items():
            oee_stats[stat] = method(data)

        return oee_stats

    # region run_stats_methods
    @staticmethod
    def cycle_count(data: pd.DataFrame) -> int:
        """
        Returns a cycle count for the given data.
        """
        return len(data)
    
    @staticmethod
    def first_cycle(data: pd.DataFrame) -> pd.DatetimeIndex:
        """
        Returns DatetimeIndex of the first data cycle.
        """
        return min(data.index)

    @staticmethod
    def last_cycle(data: pd.DataFrame) -> pd.DatetimeIndex:
        """
        Returns DatetimeIndex of the last data cycle.
        """
        return max(data.index)

    @staticmethod
    def total_time(data: pd.DataFrame) -> float:
        """
        Returns the time difference (in seconds)
        between the first and last cycle.
        """
        return (
            data['timestamp'].loc(ProductInspect.last_cycle(data))
            - data['timestamp'].loc(ProductInspect.first_cycle(data))
            )

    @staticmethod
    def part_cycles(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns non-empty poucher cycles for the given data.
        """
        return data[data['part_present'] == 1]

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
    def first_part(data: pd.DataFrame) -> pd.DatetimeIndex:
        """
        Returns DatetimeIndex of the first part made.
        """
        return min(data[data['part_present'] == 1].index)

    @staticmethod
    def last_part(data: pd.DataFrame) -> pd.DatetimeIndex:
        """
        Returns DatetimeIndex of the last part made.
        """
        return max(data[data['part_present'] == 1].index)

    @staticmethod
    def production_time(data: pd.DataFrame) -> float:
        """
        Returns the time difference (in seconds)
        between the first part and last part.
        """
        return (
            data['timestamp'].loc(ProductInspect.last_part(data))
            - data['timestamp'].loc(ProductInspect.first_part(data))
            )

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
        Returns the number of parts with duplicate serial numbers.
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
    pass

    # region stop_stats_methods
    @staticmethod
    def stops(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns all cycles which exceed maximum cycle time.
        """
        return data[data['cycle_time'] > ProductInspect.MAX_CYCLE_TIME]

    @staticmethod
    def total_stop_count(data: pd.DataFrame) -> int:
        """
        Returns the number of stops for the given data.
        """
        return len(ProductInspect.stops(data))

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
            - ProductInspect.total_stop_time(data)
            )

    @staticmethod
    def uptime_percentage(data: pd.DataFrame) -> float:
        """
        Returns the decimal percentage of uptime for the given data.
        """
        return (
            ProductInspect.total_run_time(data)
            / ProductInspect.total_time(data)
            )

    @staticmethod
    def short_stops(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns all stops with duration shorter than SHORT_STOP_CUTOFF.
        """
        return data.drop(
            (
                data['cycle_time'] > ProductInspect.OEE_STOP_CUTOFF
                and data['cycle_time'] < ProductInspect.MAX_CYCLE_TIME
                ).index
            )

    @staticmethod
    def short_stop_count(data: pd.DataFrame) -> int:
        """
        Returns the number of short stops for the given data.
        """
        return len(ProductInspect.short_stops(data))

    @staticmethod
    def short_stop_time(data: pd.DataFrame) -> float:
        """
        Returns the total time in seconds of all
        short stops for the given data.
        """
        return sum((ProductInspect.short_stops(data)).loc['cycle_time'])

    @staticmethod
    def long_stops(data: pd.DataFrame) -> pd.DataFrame:
        """
        Returns all stops with duration longer than 2 minutes.
        """
        return data.drop(
            (
                data['cycle_time'] < ProductInspect.OEE_STOP_CUTOFF
                ).index
        )

    @staticmethod
    def long_stop_count(data: pd.DataFrame) -> int:
        """
        Returns the number of long stops for the given data.
        """
        return len(ProductInspect.long_stops(data))

    @staticmethod
    def long_stop_time(data: pd.DataFrame) -> float:
        """
        Returns the total time in seconds of all
        long stops for the given data.
        """
        return sum((ProductInspect.long_stops(data)).loc['cycle_time'])
    # endregion
    pass

    # region oee_stats_methods
    @staticmethod
    def oee_run_time(data: pd.DataFrame) -> float:
        """
        Returns OEE Net Run Time, which ignores stops
        with a duration shorter than OEE_STOP_CUTOFF.
        """
        return (
            ProductInspect.total_run_time(data)
            + ProductInspect.short_stop_time(data)
        )

    @staticmethod
    def availability_rate(data: pd.DataFrame) -> float:
        """
        Returns the OEE Availability Rate for the given data
        as a decimal percentage.
        """
        return (
            ProductInspect.oee_run_time(data)
            / ProductInspect.total_time(data)
        )

    @staticmethod
    def performance_rate(data: pd.DataFrame) -> float:
        """
        Returns the OEE Performance Rate for the given data
        as a decimal percentage.
        """
        return (
            ProductInspect.part_count(data)
            / ProductInspect.oee_run_time(data)
            / ProductInspect.IDEAL_RUN_RATE
            / 60
        )

    @staticmethod
    def quality_rate(data: pd.DataFrame) -> float:
        """
        Returns the OEE Quality Rate for the given data
        as a decimal percentage.
        
        Note: This only accounts for reworks, not rejected pouches. 
        It's assumed losses due to print defects and melted product
        are minimal, but this is not always the case.
        """
        return 1 - (
            ProductInspect.rework_count(data)
            / ProductInspect.part_count(data)       
        )

    @staticmethod
    def oee_rate(data: pd.DataFrame) -> float:
        """
        Returns the OEE for the given data as a decimal percentage.
        """
        return (
            ProductInspect.availability_rate(data)
            * ProductInspect.performance_rate(data)
            * ProductInspect.quality_rate(data)
        )

    # endregion
    pass

    # endregion
    pass

