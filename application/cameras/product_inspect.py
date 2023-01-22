from __future__ import annotations

import datetime
import os
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import Any

import numpy as np
import pandas as pd

from application.cameras import ProcessData


@dataclass
class ProductInspectCamera:
    """
    iTrak Poucher Product Inspect Camera object.
    """
    _machine_info: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._data_folder = self.machine_info.get('data_folder')
        self._process_vars = self.PROCESS_VARS
        self._process_code = self.process_vars['PROCESS_CODE']

    # region process_info

    RAW_DATA_HEADERS = [
        "item_number", "lot_number", "serial_number",
        "part_present", "cognex_timestamp"
        ]

    PROCESS_VARS = {

        'PROCESS_CODE': 'PR',

        # throughput information
        'PARTS_PER_CYCLE': 1,

        # machine rates [/sec]
        'IDEAL_RATE_HZ': 8400 / 3600,
        'STANDARD_RATE_HZ': 5000 / 3600,

        # stop duration information [s]
        'MAX_CYCLE_TIME_SECONDS': 1.1,
        'SHORT_STOP_LIMIT_SECONDS': 120,
        'SHORT_STOP_BIN_WIDTH_SECONDS': 2,
        'LONG_STOP_BIN_WIDTH_SECONDS': 60
        }
    # endregion
    ...

    # region properties
    @property
    def machine_info(self) -> dict:
        return self._machine_info

    @property
    def data_folder(self) -> str:
        return self._data_folder

    @property
    def process_code(self) -> str:
        return self._process_code

    @property
    def process_vars(self) -> dict:
        return self._process_vars

    @property
    def cached_data(self) -> dict:
        return self._cached_data
    # endregion
    ...

    # region methods
    def _to_cache(self, key_: datetime.date, data_: pd.DataFrame) -> None:
        """
        Stores the given datetime key and process data in a
        cached DataFrame for further use.
        """
        self._cached_data.update({key_: data_})

    def new_block(
        self, start_datetime: dt, end_datetime: dt
        ) -> ProductInspectData:
        """
        Returns a DataBlock object of process data for the given timespan.
        """
        _t = dt.now()

        print(
            f'\n\nCreating DataBlock for {self.__str__()}: '
            f'{start_datetime} - {end_datetime}\n'
            )

        data_ = self._concatenate_days(
            pd.date_range(start_datetime, end_datetime, freq='d')
        )

        print(
            f'Retrieved data with length '
            f'{len(data_.index)} in {dt.now() - _t}'
            )

        return ProductInspectData(self, data_, start_datetime, end_datetime)

    def _concatenate_days(self, days: pd.DatetimeIndex) -> pd.DataFrame:
        """
        Fetch the data for each item in dates.
        """
        data_ = pd.DataFrame()
        for day_ in days.to_pydatetime():
            data_ = pd.concat([data_, self.load_data(day_)])

        return data_

    def load_data(self, date_: dt) -> pd.DataFrame:
        """
        Returns cached data if it exists, otherwise loads 
        the data from process data files.
        """
        key_ = datetime.date(date_.year, date_.month, date_.day)

        try:
            return self.cached_data[key_]

        except AttributeError:
            self._cached_data = {}
            self._to_cache(key_, self._load_data_from_file(date_))
            return self.cached_data[key_]

        except KeyError:
            self._to_cache(key_, self._load_data_from_file(date_))
            return self.cached_data[key_]

    def _load_data_from_file(self, date_: dt) -> pd.DataFrame:
        """
        Loads process data file for the given day.
        """
        target_file = (
            f'{self.data_folder}/{self.process_code}{date_:%Y%m%d}.txt'
            )

        return ProcessData.load(target_file, self.RAW_DATA_HEADERS)

    def __str__(self) -> str:
        return (f'{self.data_folder}-{self.process_code}')
    # endregion
    ...

@dataclass
class ProductInspectData:
    """
    Object for handling data logged by the
    iTrak Poucher Product Inspect Camera.
    """
    _data_source: ProductInspectCamera
    _data: pd.DataFrame
    _start_datetime: dt
    _end_datetime: dt

    def __post_init__(self) -> None:
        if self.data.empty:
            raise Exception("Empty DataBlock Created.")
        self._init_vars()

    def __str__(self) -> str:
        return (
            f'{self._data_source}_'
            f'{self._start_datetime:%Y%m%d-%H%M%S}-'
            f'{self._end_datetime:%Y%m%d-%H%M%S}'
        )

    # region dicts
    def _init_vars(self) -> None:
        """
        Initializes variables, properties,
        and dictionaries used within this class.
        """
        self._process_vars = deepcopy(self.data_source.process_vars)
        self._process_code = self.process_vars['PROCESS_CODE']

        self._cycle_stats_dict = {

            'first_cycle': self.first_cycle,
            'last_cycle': self.last_cycle,

            'all_cycle_time': self.all_cycle_time,
            'cycle_count': self.cycle_count,
        }

        self._parts_stats_dict = {

            'part_count': self.part_count,
            'first_part': self.first_part,
            'last_part': self.last_part,
            'productive_time': self.productive_time,

            'empty_count': self.empty_count,
            'empty_rate': self.empty_rate,

            'rework_count': self.rework_count,
            'rework_rate': self.rework_rate
        }

        self._stops_stats_dict = {

            'total_stop_count': self.total_stop_count,
            'total_stop_time': self.total_stop_time,
            'total_run_time': self.total_run_time,
            'uptime_percentage': self.uptime_percentage,

            'short_stop_count': self.short_stop_count,
            'short_stop_time': self.short_stop_time,

            'long_stop_count': self.long_stop_count,
            'long_stop_time': self.long_stop_time,
        }

        self._oee_stats_dict = {

            'oee_run_time': self.oee_run_time,

            'availability_rate': self.availability_rate,
            'performance_rate': self.performance_rate,
            'quality_rate': self.quality_rate,

            'oee_rate': self.oee_rate
        }
    # endregion
    ...

    # region properties
    @property
    def data_source(self) -> ProductInspectCamera:
        return self._data_source

    @property
    def data(self) -> pd.DataFrame:
        return self._data

    @property
    def process_code(self) -> str:
        return self._process_code

    @property
    def process_vars(self) -> dict:
        return self._process_vars

    @property
    def all_stats(self) -> dict:
        try:
            return self._all_stats
        except AttributeError:
            self._run_all_stats()
            return self._all_stats

    @property
    def cycle_stats(self) -> dict:
        try:
            return self._cycle_stats
        except AttributeError:
            self._run_cycle_stats()
            return self._cycle_stats

    @property
    def parts_stats(self) -> dict:
        try:
            return self._parts_stats
        except AttributeError:
            self._run_parts_stats()
            return self._parts_stats
    
    @property
    def stops_stats(self) -> dict:
        try:
            return self._stops_stats
        except AttributeError:
            self._run_stops_stats()
            return self._stops_stats

    @property
    def oee_stats(self) -> dict:
        try:
            return self._oee_stats
        except AttributeError:
            self._run_oee_stats()
        return self._oee_stats
    # endregion
    ...

    # region stats
    def _run_all_stats(self) -> None:
        """
        Calls the corresponding method for each group of stats.
        """
        _t = dt.now()
        print(f'{_t}: Running all stats...\t\t\t', end='')

        self._all_stats = (
            self.cycle_stats
            | self.parts_stats
            | self.stops_stats
            | self.oee_stats
            )
        print(f'Done in {dt.now() - _t}')

    def _run_cycle_stats(self) -> None:
        """
        Calculates statistics related to all machine cycles for the datablock.
        """
        self._cycle_stats = {}
        for key_, method_ in self._cycle_stats_dict.items():
            self._cycle_stats[key_] = method_

    def _run_parts_stats(self) -> None:
        """
        Calculates statistics related to parts made for the datablock.
        """
        self._parts_stats = {}
        for key_, method_ in self._parts_stats_dict.items():
            self._parts_stats[key_] = method_

    def _run_stops_stats(self) -> None:
        """
        Calculates statistics related to machine stops for the datablock.
        """
        self._stops_stats = {}
        for key_, method_ in self._stops_stats_dict.items():
            self._stops_stats[key_] = method_

    def _run_oee_stats(self) -> None:
        """
        Calculates statistics related to OEE for the data.
        """
        self._oee_stats = {}
        for key_, method_ in self._oee_stats_dict.items():
            self._oee_stats[key_] = method_

    # region cycle_stats
    @property
    def first_cycle(self) -> pd.Timestamp:
        """
        Returns time of first cycle for the given data.
        """
        try:
            return self._first_cycle
        except AttributeError:
            self._first_cycle = min(self.data.index)
        
        return self.first_cycle

    @property
    def last_cycle(self) -> pd.Timestamp:
        """
        Returns time of last cycle for the given data.
        """
        try:
            return self._last_cycle
        except AttributeError:
            self._last_cycle = max(self.data.index)

        return self.last_cycle

    @property
    def all_cycle_time(self) -> float:
        """
        Returns the time difference (in seconds)
        between the first and last cycle.
        """
        try:
            return self._all_cycle_time
        except AttributeError:
            self._all_cycle_time = (
                self.last_cycle - self.first_cycle
                ).total_seconds()

        return self.all_cycle_time

    @property
    def cycle_count(self) -> int:
        """
        Returns a cycle count for the given data.
        """
        try:
            return self._cycle_count
        except AttributeError:
            self._cycle_count = len(self.data.index)

        return self.cycle_count
    # endregion
    ...

    # region parts_stats
    @property
    def parts(self) -> pd.DataFrame:
        """
        Returns non-empty poucher cycles for the data.
        """
        try:
            return self._parts
        except AttributeError:
            self._parts = self.data[self.data['part_present'] == 1]
            return self._parts

    @property
    def first_part(self) -> pd.Timestamp:
        """
        Returns the DatetimeIndex of the first part made.
        """
        try:
            return self._first_part
        except AttributeError:
            self._first_part = min(
                self.data[self.data['part_present'] == 1].index
                )
            return self._first_part

    @property
    def last_part(self) -> pd.Timestamp:
        """
        Returns the DatetimeIndex of the last part made.
        """
        try:
            return self._last_part
        except AttributeError:
            self._last_part = max(
                self.data[self.data['part_present'] == 1].index
                )
            return self._last_part

    @property
    def productive_time(self) -> float:
        """
        Returns the time duration (in seconds)
        between the first part and last part.
        """
        try:
            return self._productive_time
        except AttributeError:
            self._productive_time = (
                self.last_part - self.first_part
            ).total_seconds()
            return self._productive_time

    @property
    def part_count(self) -> int:
        """
        Returns the number of non-empty cycles for the data.
        """
        try:
            return self._part_count
        except AttributeError:
            self._part_count = len(self.parts.index)
            return self._part_count

    @property
    def empty_cycles(self) -> pd.DataFrame:
        """
        Returns all cycles with no part present.
        """
        try:
            return self._empty_cycles
        except AttributeError:
            self._empty_cycles = self.data[self.data['part_present'] == 0]
            return self._empty_cycles

    @property
    def empty_count(self) -> int:
        """
        Returns the number of empty cycles for the data.
        """
        try:
            return self._empty_count
        except AttributeError:
            self._empty_count = len(self.empty_cycles.index)
            return self._empty_count

    @property
    def empty_rate(self) -> float:
        """
        Returns the decimal percentage of empty cycles for the data.
        """
        try:
            return self._empty_rate
        except AttributeError:
            self._empty_rate = self.empty_count / self.cycle_count
            return self._empty_rate

    @property
    def reworks(self) -> pd.DataFrame:
        """
        Returns all cycles with duplicate serial numbers.
        """
        try:
            return self._reworks
        except AttributeError:
            self._reworks = self.data[
                self.data.duplicated('serial_number')
                ]
            return self._reworks

    @property
    def rework_count(self) -> int:
        """
        Returns the number of parts with duplicate serial numbers.
        """
        try:
            return self._rework_count
        except AttributeError:
            self._rework_count = len(self.reworks.index)
            return self._rework_count

    @property
    def rework_rate(self) -> float:
        """
        Returns the decimal percentage of reworked parts.
        """
        try:
            return self._rework_rate
        except AttributeError:
            self._rework_rate = self.rework_count / self.cycle_count
            return self._rework_rate
    # endregion
    ...

    # region stop_stats
    @property
    def stops(self) -> pd.DataFrame:
        """
        Returns all cycles which exceed maximum cycle time.
        """
        try:
            return self._stops
        except AttributeError:
            self._stops = (
                self.data[self.data['cycle_time']
                > self.process_vars['MAX_CYCLE_TIME_SECONDS']]
            )
            return self._stops


    @property
    def run_cycles(self) -> pd.DataFrame:
        """
        Returns all cycles which do not exceed maximum cycle time.
        """
        try:
            return self._run_cycles
        except AttributeError:
            self._run_cycles = (
                self.data[self.data['cycle_time']
                < self.process_vars['MAX_CYCLE_TIME_SECONDS']]
            )
            return self._run_cycles

    @property
    def total_stop_count(self) -> int:
        """
        Returns the number of stops for the given data.
        """
        try:
            return self._total_stop_count
        except AttributeError:
            self._total_stop_count = len(self.stops.index)
            return self._total_stop_count

    @property
    def total_stop_time(self) -> float:
        """
        Returns the sum of cycle times greater than the maximum.
        """
        try:
            return self._total_stop_time
        except AttributeError:
            self._total_stop_time = sum(self.stops['cycle_time'])
            return self._total_stop_time

    @property
    def total_run_time(self) -> float:
        """
        Returns the sum of cycle times less than the maximum.
        """
        try:
            return self._total_run_time
        except AttributeError:
            self._total_run_time = sum(self.run_cycles['cycle_time'])
            return self._total_run_time

    @property
    def uptime_percentage(self) -> float:
        """
        Returns the decimal percentage of uptime for the data.
        """
        try:
            return self._uptime_percentage
        except AttributeError:
            self._uptime_percentage = (
                self.total_run_time / self.all_cycle_time
                )
            return self._uptime_percentage

    @property
    def short_stops(self) -> pd.DataFrame:
        """
        Returns all stops with duration shorter than SHORT_STOP_LIMIT.
        """
        try:
            return self._short_stops
        except AttributeError:
            drop_rows = pd.concat([
                self.data[self.data['cycle_time']
                > self.process_vars['SHORT_STOP_LIMIT_SECONDS']],
                self.data[self.data['cycle_time']
                < self.process_vars['MAX_CYCLE_TIME_SECONDS']]
            ]).index
            self._short_stops = self.data.drop(drop_rows).dropna()
            return self._short_stops

    @property
    def short_stop_count(self) -> int:
        """
        Returns the number of short stops for the data.
        """
        try:
            return self._short_stop_count
        except AttributeError:
            self._short_stop_count = len(self.short_stops.index)
            return self._short_stop_count

    @property
    def short_stop_time(self) -> float:
        """
        Returns the total time in seconds of all short stops.
        """
        try:
            return self._short_stop_time
        except AttributeError:
            self._short_stop_time = sum(self.short_stops['cycle_time'])
            return self._short_stop_time

    @property
    def long_stops(self) -> pd.DataFrame:
        """
        Returns all stops with duration longer than SHORT_STOP_LIMIT.
        """
        try:
            return self._long_stops
        except AttributeError:
            drop_rows = self.data[
                self.data['cycle_time']
                < self.process_vars['SHORT_STOP_LIMIT_SECONDS']
                ].index
            self._long_stops = self.data.drop(drop_rows).dropna()
            return self._long_stops
    
    @property
    def long_stop_count(self) -> int:
        """
        Returns the number of long stops for the data.
        """
        try:
            return self._long_stop_count
        except AttributeError:
            self._long_stop_count = len(self.long_stops.index)
            return self._long_stop_count

    @property
    def long_stop_time(self) -> float:
        """
        Returns the total time in seconds of all long stops.
        """
        try:
            return self._long_stop_time
        except AttributeError:
            self._long_stop_time = sum(self.long_stops['cycle_time'])
        return self._long_stop_time
    # endregion
    ...

    # region oee_stats
    @property
    def oee_run_time(self) -> float:
        """
        Returns OEE Net Run Time, which ignores stops
        with a duration shorter than SHORT_STOP_LIMIT.
        """
        try:
            return self._oee_run_time
        except AttributeError:
            self._oee_run_time = self.total_run_time + self.short_stop_time
            return self._oee_run_time

    @property
    def availability_rate(self) -> float:
        """
        Returns the OEE Availability Rate for the data
        as a decimal percentage.
        """
        try:
            return self._availability_rate
        except AttributeError:
            self._availability_rate = (
                self.oee_run_time
                / self.all_cycle_time
            )
            return self.availability_rate

    @property
    def performance_rate(self) -> float:
        """
        Returns the OEE Performance Rate for the data
        as a decimal percentage.
        """
        try:
            return self._performance_rate
        except AttributeError:
            self._performance_rate = (
                (self.part_count / self.oee_run_time)
                / (self.process_vars['IDEAL_RATE_HZ'] / 60)
            )
            return self._performance_rate

    @property
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
            self._quality_rate = (1 - (self.rework_count / self.part_count))
            return self._quality_rate

    @property
    def oee_rate(self) -> float:
        """
        Returns the OEE for the data as a decimal percentage.
        """
        try:
            return self._oee_rate
        except AttributeError:
            self._oee_rate = (
                self.availability_rate
                * self.performance_rate
                * self.quality_rate
                )
            return self._oee_rate
    # endregion
    ...
    # endregion
    ...

    # region to_excel
    def stats_to_xls(self) -> None:
        """
        Dumps the stats DataFrame to .xlsx file.
        """
        file_ = f'{self.__str__()}_Stats.xlsx'
        folder_ = f'.test_out/xls/{self._data_source.__str__()}/'
        path_ = folder_ + file_

        if not os.path.exists(folder_):
            os.mkdir(folder_)

        pd.DataFrame(
                self.all_stats.values(), columns=[self.__str__()],
                index=self.all_stats.keys()
            ).T.to_excel(path_)

    def stops_to_xls(self) -> None:
        """
        Dumps the stops DataFrame to .xlsx file.
        """
        file_ = f'{self.__str__()}_Stops.xlsx'
        folder_ = f'.test_out/xls/{self._data_source.__str__()}/'
        path_ = folder_ + file_

        if not os.path.exists(folder_):
            os.mkdir(folder_)

        self._stops.to_excel(path_)
    # endregion
    ...

    # region productivity
    @property
    def productivity(self, freq: str='s') -> pd.DataFrame:
        """
        Returns production yields vs. standard yields
        at the given frequency (default per second).
        """
        _t = dt.now()
        print(f'{_t}: Getting productivity...\t\t\t', end='')

        try:
            return self._productivity[freq]
        except AttributeError:
            self._productivity = {}
            self._productivity[freq] = self._get_productivity(freq)
            return self._productivity[freq]
        except KeyError:
            self._productivity[freq] = self._get_productivity(freq)
            return self._productivity[freq]
        finally:
            print(f'Done in {dt.now() - _t}')

    def _get_productivity(self, freq: str) -> pd.DataFrame:
        """
        Returns the productivity at each interval
        of the given frequency.
        """
        datetime_range = pd.date_range(
                self._start_datetime, self._end_datetime, freq=freq
                )
        range_size = len(datetime_range)
        columns = ['actual_yield', 'standard_yield', 'rate_Hz']
        prod_ = pd.DataFrame(
            data=np.zeros((len(datetime_range), len(columns))),
            index=datetime_range, columns=columns
        )

        try:
            period_length = (prod_.index[-1].to_datetime64() - prod_.index[0].to_datetime64()) / len(prod_)
        except IndexError:
            raise Exception("Index out of bounds for the given data.")

        freq_factor = pd.Timedelta(period_length) / pd.Timedelta(seconds=1)

        prod_['standard_yield'] = (
            np.arange(range_size)
            * self.process_vars['STANDARD_RATE_HZ']
            * freq_factor
        )

        prod_['actual_yield'] = (
            self.running_part_count().sort_index().reindex_like(
                datetime_range.to_series(), method='ffill'
                ).fillna(0)
        )

        prod_['rate_Hz'] = prod_['actual_yield'].diff() / freq_factor

        return prod_

    def running_part_count(self) -> pd.Series:
        """
        Returns a Series with a running part count.
        """
        self.data['part_count'] = self.data['part_present'].cumsum()
        return self.data['part_count']

    def prod_to_xls(self) -> None:
        """
        Dumps the productivity DataFrame to .xlsx file.
        """
        file_ = f'{self.__str__()}_Productivity.xlsx'
        folder_ = f'.test_out/xls/{self._data_source.__str__()}/'
        path_ = folder_ + file_

        if not os.path.exists(folder_):
            os.mkdir(folder_)

        self._stops.to_excel(path_)
    # endregion
    ...
