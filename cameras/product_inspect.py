from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime as dt

import pandas as pd
import numpy as np

from cameras import Camera
from datafiles import DataBlock, ProcessData


class ProductInspectCamera(Camera):
    """
    iTrak Poucher Product Inspect Camera object.
    """

    def __init__(self, machine_info: dict) -> None:
        self.machine_info = machine_info
        self.data_folder = self.machine_info.get('data_folder')

    def load_data(
        self, start_datetime: dt, end_datetime: dt
        ) -> ProductInspectData:
        """
        Returns a DataBlock object of process data for the given timespan.
        """
        return ProductInspectData(
            self.data_folder, start_datetime, end_datetime
            )


@dataclass
class ProductInspectData(DataBlock):
    """
    DataBlock subclass for handling data logged by the
    iTrak Poucher Product Inspect Camera.
    """
    data_folder: str
    start_datetime: dt
    end_datetime: dt

    # region process_parameters
    PROCESS_CODE = 'PR'
    PARTS_PER_CYCLE = 1

    # machine rates [/sec]
    IDEAL_RATE_PER_S = 8400 / 3600
    STANDARD_RATE_PER_S = 5000 / 3600

    # stop duration information [s]
    MAX_CYCLE_TIME = 1.1
    SHORT_STOP_LIMIT = 120
    SHORT_STOP_BIN_WIDTH = 2
    LONG_STOP_BIN_WIDTH = 60

    RAW_DATA_HEADERS = [
        "item_number", "lot_number", "serial_number",
        "part_present", "cognex_timestamp"
        ]
    # endregion
    ...

    def __post_init__(self) -> None:
        self.data()

    def __repr__(self) -> str:
        return (
            f'{self.data_folder}-{self.PROCESS_CODE}__'
            f'{self.start_datetime:%Y%m%d-%H%M%S}_'
            f'{self.end_datetime:%Y%m%d-%H%M%S}'
        )

    def load_data(self) -> pd.DataFrame:
        return ProcessData.load(
            self.data_folder, ProductInspectData.PROCESS_CODE,
            self.start_datetime, self.end_datetime,
            ProductInspectData.RAW_DATA_HEADERS
        )

    def data(self) -> pd.DataFrame:
        try:
            return self._data
        except AttributeError:
            self._data = self.load_data()
            self.cycle_times()
            self.cycle_rates()
            return self._data

    def stats(self) -> pd.DataFrame:
        try:
            return self._stats
        except AttributeError:
            self._stats = pd.concat(
                [
                    self.run_stats(),
                    self.stop_stats(),
                    self.oee_stats()
                ], axis=1,
            )
            return self._stats

    # region stats
    def run_stats(self) -> pd.DataFrame:
        """
        Returns run statistics for the data.
        """

        RUN_STATS_DICT = {
            'total_cycles': self.cycle_count(),
            'total_time': self.total_time(),

            'parts_pouched': self.part_count(),
            'first_part_pouched': self.first_part(),
            'last_part_pouched': self.last_part(),
            'production_time': self.production_time(),

            'empty_count': self.empty_count(),
            'empty_rate': self.empty_rate(),

            'rework_count': self.rework_count(),
            'rework_rate': self.rework_rate()
        }

        try:
            return self._run_stats

        except AttributeError:
            self._run_stats = pd.DataFrame(
                columns=RUN_STATS_DICT.keys(), index=[self.__repr__()]
                )
            for stat, method in RUN_STATS_DICT.items():
                self._run_stats[stat] = method
            return self._run_stats

    def stop_stats(self) -> pd.DataFrame:
        """
        Returns stop statistics for the data.
        """

        STOP_STATS_DICT = {
            'total_stop_count': self.total_stop_count(),
            'total_stop_time': self.total_stop_time(),
            'total_run_time': self.total_run_time(),

            'short_stop_count': self.short_stop_count(),
            'short_stop_time': self.short_stop_time(),

            'long_stop_count': self.long_stop_count(),
            'long_stop_time': self.long_stop_time(),
        }

        try:
            return self._stop_stats

        except AttributeError:
            self._stop_stats = pd.DataFrame(
                columns=STOP_STATS_DICT.keys(), index=[self.__repr__()]
                )
            for stat, method in STOP_STATS_DICT.items():
                self._stop_stats[stat] = method
            return self._stop_stats
    
    def oee_stats(self) -> pd.DataFrame:
        """
        Returns OEE statistics for the data.
        """

        OEE_STATS_DICT = {
            'oee_run_time': self.oee_run_time(),

            'availability_rate': self.availability_rate(),
            'performance_rate': self.performance_rate(),
            'quality_rate': self.quality_rate(),

            'oee_rate': self.oee_rate()
        }

        try:
            return self._oee_stats

        except AttributeError:
            self._oee_stats = pd.DataFrame(
                columns=OEE_STATS_DICT.keys(), index=[self.__repr__()]
                )
            for stat, method in OEE_STATS_DICT.items():
                self._oee_stats[stat] = method
            return self._oee_stats

    # region run_stats
    def parts(self) -> pd.DataFrame:
        """
        Returns non-empty poucher cycles for the data.
        """
        try:
            return self._parts
        except AttributeError:
            self._parts = self.data()[self.data()['part_present'] == 1]
            return self._parts

    def part_count(self) -> int:
        """
        Returns the number of non-empty cycles for the data.
        """
        try: 
            return self._part_count
        except AttributeError:
            self._part_count = len(self.parts().index)
            return self._part_count

    def running_part_count(self) -> pd.Series:
        """
        Returns a Series with a running part count.
        """
        try:
            self.data()['part_count'] = self.data()['part_present'].cumsum()
        except Exception:
            pass
        finally:
            return self.data()['part_count']

    def first_part(self) -> pd.DatetimeIndex:
        """
        Returns the DatetimeIndex of the first part made.
        """
        try:
            return self._first_part
        except AttributeError:
            self._first_part = min(
                self.data()[self.data()['part_present']  == 1].index
                )
            return self._first_part
    
    def last_part(self) -> pd.DatetimeIndex:
        """
        Returns the DatetimeIndex of the last part made.
        """
        try:
            return self._last_part
        except AttributeError:
            self._last_part = max(
                self.data()[self.data()['part_present']  == 1].index
                )
            return self._last_part

    def production_time(self) -> float:
        """
        Returns the time difference (in seconds)
        between the first part and last part.
        """
        try:
            return self._production_time
        except AttributeError:
            self._production_time = (
                self.last_part() - self.first_part()
                ).total_seconds()
            return self._production_time

    def empty_cycles(self) -> pd.DataFrame:
        """
        Returns all cycles with no part present.
        """
        try:
            return self._empty_cycles
        except AttributeError:
            self._empty_cycles = self.data()[self.data()['part_present'] == 0]
            return self._empty_cycles

    def empty_count(self) -> int:
        """
        Returns the number of empty cycles for the data.
        """
        try:
            return self._empty_count
        except AttributeError:
            self._empty_count = len(self.empty_cycles().index)
            return self._empty_count

    def empty_rate(self) -> float:
        """
        Returns the decimal percentage of empty cycles for the data.
        """
        try:
            return self._empty_rate
        except AttributeError:
            self._empty_rate = (self.empty_count() / self.cycle_count())
            return self._empty_rate

    def reworks(self) -> pd.DataFrame:
        """
        Returns all cycles with duplicate serial numbers.
        """
        try:
            return self._reworks
        except AttributeError:
            self._reworks = self.data()[
                self.data().duplicated('serial_number')
                ]
            return self._reworks

    def rework_count(self) -> int:
        """
        Returns the number of parts with duplicate serial numbers.
        """
        try:
            return self._rework_count
        except AttributeError:
            self._rework_count = len(self.reworks().index)
            return self._rework_count

    def rework_rate(self) -> float:
        """
        Returns the decimal percentage of reworked parts.
        """
        try:
            return self._rework_rate
        except AttributeError:
            self._rework_rate = (
                self.rework_count()
                / self.cycle_count()
            )
            return self._rework_rate
    # endregion
    ...

    # region stop_stats
    def stops(self) -> pd.DataFrame:
        """
        Returns all cycles which exceed maximum cycle time.
        """
        try:
            return self._stops
        except AttributeError:
            self._stops = (
                self.data()[self.data()['cycle_time']
                > self.MAX_CYCLE_TIME]
            )
            return self._stops

    def run_cycles(self) -> pd.DataFrame:
        """
        Returns all cycles which do not exceed maximum cycle time.
        """
        try:
            return self._run_cycles
        except AttributeError:
            self._run_cycles = (
                self.data()[self.data()['cycle_time']
                < self.MAX_CYCLE_TIME]
            )
            return self._run_cycles

    def total_stop_count(self) -> int:
        """
        Returns the number of stops for the given data.
        """
        try:
            return self._total_stop_count
        except AttributeError:
            self._total_stop_count = len(self.stops().index)
            return self._total_stop_count

    def total_stop_time(self) -> float:
        """
        Returns the sum of cycle times greater than the maximum.
        """
        try:
            return self._total_stop_time
        except AttributeError:
            self._total_stop_time = sum(self.stops()['cycle_time'])
            return self._total_stop_time

    def total_run_time(self) -> float:
        """
        Returns the sum of cycle times less than the maximum.
        """
        try:
            return self._total_run_time
        except AttributeError:
            self._total_run_time = sum(
                self.run_cycles()['cycle_time']
            )
            return self._total_run_time

    def uptime_percentage(self) -> float:
        """
        Returns the decimal percentage of uptime for the data.
        """
        try:
            return self._uptime_percentage
        except AttributeError:
            self._uptime_percentage = (
                self.total_run_time() / self.total_time()
                )
            return self._uptime_percentage

    def short_stops(self) -> pd.DataFrame:
        """
        Returns all stops with duration shorter than SHORT_STOP_LIMIT.
        """
        try:
            return self._short_stops
        except AttributeError:
            drop_rows = pd.concat([
                self.data()[self.data()['cycle_time'] > self.SHORT_STOP_LIMIT],
                self.data()[self.data()['cycle_time'] < self.MAX_CYCLE_TIME]
                ]).index
            self._short_stops = self.data().drop(drop_rows).dropna()
            return self._short_stops

    def short_stop_count(self) -> int:
        """
        Returns the number of short stops for the data.
        """
        try:
            return self._short_stop_count
        except AttributeError:
            self._short_stop_count = len(self.short_stops().index)
            return self._short_stop_count

    def short_stop_time(self) -> float:
        """
        Returns the total time in seconds of all short stops.
        """
        try:
            return self._short_stop_time
        except AttributeError:
            self._short_stop_time = sum(self.short_stops()['cycle_time'])
            return self._short_stop_time

    def long_stops(self) -> pd.DataFrame:
        """
        Returns all stops with duration longer than SHORT_STOP_LIMIT.
        """
        try:
            return self._long_stops
        except AttributeError:
            drop_rows = self.data()[self.data()['cycle_time'] < self.SHORT_STOP_LIMIT].index
            self._long_stops = self.data().drop(drop_rows).dropna()
            return self._long_stops
    
    def long_stop_count(self) -> int:
        """
        Returns the number of long stops for the data.
        """
        try:
            return self._long_stop_count
        except AttributeError:
            self._long_stop_count = len(self.long_stops().index)
            return self._long_stop_count

    def long_stop_time(self) -> float:
        """
        Returns the total time in seconds of all long stops.
        """
        try:
            return self._long_stop_time
        except AttributeError:
            self._long_stop_time = sum(self.long_stops()['cycle_time'])
            return self._long_stop_time
    # endregion
    ...

    # region oee_stats
    def oee_run_time(self) -> float:
        """
        Returns OEE Net Run Time, which ignores stops
        with a duration shorter than SHORT_STOP_LIMIT.
        """
        try:
            return self._oee_run_time
        except AttributeError:
            self._oee_run_time = (
                self.total_run_time() + self.short_stop_time()
            )
            return self._oee_run_time

    def availability_rate(self) -> float:
        """
        Returns the OEE Availability Rate for the data
        as a decimal percentage.
        """
        try:
            return self._availability_rate
        except AttributeError:
            self._availability_rate = (
                self.oee_run_time()
                / self.total_time()
            )
            return self._availability_rate

    def performance_rate(self) -> float:
        """
        Returns the OEE Performance Rate for the data
        as a decimal percentage.
        """
        try:
            return self._performance_rate
        except AttributeError:
            self._performance_rate = (
                (self.part_count() / self.oee_run_time())
                / (self.IDEAL_RATE_PER_S / 60)
            )
            return self._performance_rate

    def quality_rate(self) -> float:
        """
        Returns the OEE Quality Rate for the data
        as a decimal percentage.
        
        Note: This only accounts for reworks, not rejected pouches. 
        It's assumed losses due to melted or crushed product are minimal.
        """
        try:
            return self._quality_rate
        except AttributeError:
            self._quality_rate = (
                1 - (self.rework_count() / self.part_count())
            )
            return self._quality_rate

    def oee_rate(self) -> float:
        """
        Returns the OEE for the data as a decimal percentage.
        """
        try:
            return self._oee_rate
        except AttributeError:
            self._oee_rate = (
                self.availability_rate()
                * self.performance_rate()
                * self.quality_rate()
                )
            return self._oee_rate
    # endregion
    ...

    # endregion
    ...

    # region productivity
    def productivity(self, freq: str='s') -> pd.DataFrame:
        """
        Returns production yields vs. standard yields
        at the given frequency (default per second).
        """
        try:
            return self._productivity[freq]
        except AttributeError:
            self._productivity = dict()
            self._productivity[freq] = self.get_productivity(freq)
            return self._productivity[freq]

    def get_productivity(self, freq: str) -> pd.DataFrame:
        """
        Calculates the productivity at each interval
        of the given frequency.
        """
        datetime_range = pd.date_range(
                self.start_datetime, self.end_datetime, freq=freq
                )
        range_size = len(datetime_range)
        columns = ['actual_yield', 'standard_yield', 'rate']
        productivity = pd.DataFrame(
            data=np.zeros(shape=(range_size, len(columns))),
            index=datetime_range, columns=columns
        )

        try:
            period_length = (
                productivity.index[1].to_datetime64()
                - productivity.index[0].to_datetime64()
            )
        except IndexError:
            raise Exception("Index out of bounds for the given data.")
        
        freq_seconds = pd.Timedelta(period_length)
        frequency_multiplier = freq_seconds / pd.Timedelta(seconds =1)

        productivity['standard_yield'] = (
            np.arange(range_size)* ProductInspectData.STANDARD_RATE_PER_S
            * frequency_multiplier
        )

        productivity['actual_yield'] = (
            self.running_part_count().sort_index().reindex_like(
                datetime_range.to_series(), method='ffill'
                ).fillna(0)
        )

        productivity['rate_Hz'] = productivity['actual_yield'].diff() / frequency_multiplier

        return productivity
        # endregion
        ...
