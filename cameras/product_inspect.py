from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime as dt

import numpy as np
import pandas as pd

from cameras import DataBlock, ProcessData


@dataclass
class ProductInspectCamera:
    """
    iTrak Poucher Product Inspect Camera object.
    """
    machine_info: dict = field(default_factory=dict)

    # region process_info
    PROCESS_CODE = 'PR'

    RAW_DATA_HEADERS = [
        "item_number", "lot_number", "serial_number",
        "part_present", "cognex_timestamp"
        ]

    PROCESS_PARAMETERS_DICT = {

        # throughput information
        'PARTS_PER_CYCLE': 1,

        # machine rates [/sec]
        'IDEAL_RATE_PER_S': 8400 / 3600,
        'STANDARD_RATE_PER_S': 5000 / 3600,

        # stop duration information [s]
        'MAX_CYCLE_TIME': 1.1,
        'SHORT_STOP_LIMIT': 120,
        'SHORT_STOP_BIN_WIDTH': 2,
        'LONG_STOP_BIN_WIDTH': 60
        }
    # endregion
    ...

    def __post_init__(self) -> None:
        self.data_folder = self.machine_info.get('data_folder')
        self._params = self.PROCESS_PARAMETERS_DICT
        self._process_data = {}

    def __repr__(self) -> str:
        return (
            f'{self.data_folder}-{self.PROCESS_CODE}'
        )

    def datablock(
        self, start_datetime: dt, end_datetime: dt
        ) -> DataBlock:
        """
        Returns a DataBlock object of process data for the given timespan.
        """

        _block_data = pd.DataFrame(columns=self.RAW_DATA_HEADERS)

        block_dates = pd.date_range(
            start_datetime.date(), end_datetime.date(), freq='d'
            )

        for date in block_dates:
            _ = self.get_process_data(date)
            if _ is not None:
                pd.concat([_block_data, _])
                _.drop(_.index, inplace=True)
            else:
                continue

        return ProductInspectData(
            self, _block_data, start_datetime, end_datetime
            )

    def get_process_data(self, date: dt) -> pd.DataFrame:
        """
        Fetches process data for the given day.
        """
        try:
            return self._process_data[date]
        except KeyError:
            target_file = (
                f'{self.data_folder}/{self.PROCESS_CODE}'
                f'{date:%Y%m%d}.txt'
                )
            self._process_data[date] = ProcessData.load(
                target_file, self.RAW_DATA_HEADERS
                )
        
        if self._process_data[date].empty:
            raise Exception('Empty DataFrame Loaded.')


@dataclass
class ProductInspectData:
    """
    Object for handling data logged by the
    iTrak Poucher Product Inspect Camera.
    """
    _source: ProductInspectCamera
    _data: pd.DataFrame
    start_datetime: dt
    end_datetime: dt

    def __post_init__(self) -> None:
        self.process_code = self._source.PROCESS_CODE
        self._params = self._source._params

        if self._data.empty:
            raise Exception("Empty DataFrame.")

    def __repr__(self) -> str:
        return (
            f'{self._source}_'
            f'{self.start_datetime:%Y%m%d-%H%M%S}_'
            f'{self.end_datetime:%Y%m%d-%H%M%S}'
        )

    # region core_methods
    def data(self) -> pd.DataFrame:
        """
        Returns all cycles stored for the DataBlock.
        """
        return self._data

    def parts(self) -> pd.DataFrame:
        """
        Returns non-empty poucher cycles for the data.
        """
        try:
            return self._parts
        except AttributeError:
            self._parts = self._data[self._data['part_present'] == 1]
            return self._parts

    def empty_cycles(self) -> pd.DataFrame:
        """
        Returns all cycles with no part present.
        """
        try:
            return self._empty_cycles
        except AttributeError:
            self._empty_cycles = self._data[self._data['part_present'] == 0]
            return self._empty_cycles
    # endregion
    ...

    # region all_stats
    def all_stats(self) -> pd.DataFrame:
        try:
            return self._stats
        except AttributeError:
            self._stats = pd.concat(
                [
                    self.cycle_stats(),
                    self.parts_stats(),
                    self.stop_stats(),
                    self.oee_stats()
                ], axis=1,
            )
            return self._stats

    def cycle_stats(self) -> pd.DataFrame:
        """
        Returns cycle statistics for the datablock.
        """

        CYCLE_STATS_DICT = {

            'first_cycle': self.first_cycle(),
            'last_cycle': self.last_cycle(),

            'all_cycle_time': self.all_cycle_time(),
            'total_cycles': self.cycle_count(),
        }

        try:
            return self._cycle_stats

        except AttributeError:
            self._cycle_stats = pd.DataFrame(
                columns=CYCLE_STATS_DICT.keys(), index=[self.__repr__()]
                )
            for stat, method in CYCLE_STATS_DICT.items():
                self._cycle_stats[stat] = method
            return self._cycle_stats

    def parts_stats(self) -> pd.DataFrame:
        """
        Returns part statistics for the datablock.
        """

        PARTS_STATS_DICT = {

            'parts_processed': self.total_part_count(),
            'first_part_processed': self.first_part(),
            'last_part_processed': self.last_part(),
            'all_production_time': self.all_production_time(),

            'empty_count': self.empty_count(),
            'empty_rate': self.empty_rate(),

            'rework_count': self.rework_count(),
            'rework_rate': self.rework_rate()
        }

        try:
            return self._parts_stats
        
        except AttributeError:
            self._parts_stats = pd.DataFrame(
                columns=PARTS_STATS_DICT.keys(), index=[self.__repr__()]
            )
        for stat, method in PARTS_STATS_DICT.items():
            self._parts_stats[stat] = method
        return self._parts_stats

    def stop_stats(self) -> pd.DataFrame:
        """
        Returns stop statistics for the datablock.
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

    # region cycle_stats
    def first_cycle(self) -> pd.Timestamp:
        """
        Returns time of first cycle for the given data.
        """
        try:
            return self._first_cycle
        except AttributeError:
            self._first_cycle = min(self._data.index)
            return self._first_cycle

    def last_cycle(self) -> pd.Timestamp:
        """
        Returns time of last cycle for the given data.
        """
        try:
            return self._last_cycle
        except AttributeError:
            self._last_cycle = max(self._data.index)
            return self._last_cycle

    def all_cycle_time(self) -> float:
        """
        Returns the time difference (in seconds)
        between the first and last cycle.
        """
        try:
            return self._all_cycle_time
        except AttributeError:
            self._all_cycle_time = (
                self.last_cycle() - self.first_cycle()
            ).total_seconds()
            return self._all_cycle_time

    def cycle_count(self) -> int:
        """
        Returns a cycle count for the given data.
        """
        try:
            return self._cycle_count
        except AttributeError:
            self._cycle_count = len(self._data.index)
            return self._cycle_count
    # endregion
    ...

    # region parts_stats
    def total_part_count(self) -> int:
        """
        Returns the number of non-empty cycles for the data.
        """
        try: 
            return self._part_count
        except AttributeError:
            self._part_count = len(self.parts().index)
            return self._part_count

    def first_part(self) -> pd.Timestamp:
        """
        Returns the DatetimeIndex of the first part made.
        """
        try:
            return self._first_part
        except AttributeError:
            self._first_part = min(
                self._data[self._data['part_present']  == 1].index
                )
            return self._first_part
    
    def last_part(self) -> pd.Timestamp:
        """
        Returns the DatetimeIndex of the last part made.
        """
        try:
            return self._last_part
        except AttributeError:
            self._last_part = max(
                self._data[self._data['part_present']  == 1].index
                )
            return self._last_part

    def all_production_time(self) -> float:
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
            self._reworks = self._data[
                self._data.duplicated('serial_number')
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
                self._data[self._data['cycle_time']
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
                self._data[self._data['cycle_time']
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
                self.total_run_time() / self.all_cycle_time()
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
                self._data[self._data['cycle_time'] > self.SHORT_STOP_LIMIT],
                self._data[self._data['cycle_time'] < self.MAX_CYCLE_TIME]
                ]).index
            self._short_stops = self._data.drop(drop_rows).dropna(
                axis=0, how='cycle_time'
                )
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
            drop_rows = self._data[self._data['cycle_time'] < self.SHORT_STOP_LIMIT].index
            self._long_stops = self._data.drop(drop_rows).dropna(
                axis=0, how='cycle_time'
            )
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
                / self.all_cycle_time()
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
                (self.total_part_count() / self.oee_run_time())
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
                1 - (self.rework_count() / self.total_part_count())
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

    def running_part_count(self) -> pd.Series:
        """
        Returns a Series with a running part count.
        """
        try:
            self._data['part_count'] = self._data['part_present'].cumsum()
        except Exception:
            pass
        finally:
            return self._data['part_count']
    # endregion
    ...
