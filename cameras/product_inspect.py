from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import Any

import numpy as np
import pandas as pd

from cameras import ProcessData


@dataclass
class ProductInspectCamera:
    """
    iTrak Poucher Product Inspect Camera object.
    """
    _machine_info: dict = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        self._data_folder = self.machine_info.get('data_folder')
        self._process_code = 'PR'
        self._process_vars = self.PROCESS_VARS
        self._cached_data = {}

    # region process_info

    RAW_DATA_HEADERS = [
        "item_number", "lot_number", "serial_number",
        "part_present", "cognex_timestamp"
        ]

    PROCESS_VARS = {

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
    def cached_data(self) -> dict[pd.DataFrame]:
        return self._cached_data

    @cached_data.setter
    def cached_data(self, key_: dt.date(), data: pd.DataFrame) -> None:
        self._cached_data[key_] = data
    # endregion
    ...

    def _check_data_cache(self, key_: dt.date()) -> pd.DataFrame:
        """
        Fetches process data for the given day, first checking
        cached_data and only pulling raw data when necessary.
        """
        try:
            return self.cached_data.get(key_)
        except KeyError:
            value_ = self._load_data_from_file(key_)
            self.cached_data(key_, value_)
            return self.cached_data.get(key_)

    def new_block(
        self, start_datetime: dt, end_datetime: dt
        ) -> ProductInspectData:
        """
        Returns a DataBlock object of process data for the given timespan.
        """
        aggr_data = self._aggregate_days(
            self._parse_dates(start_datetime, end_datetime)
            )
        print(
            f'{dt.now()}: Retrieved data with length {len(aggr_data.index)}'
            )

        return ProductInspectData(
            self, aggr_data, start_datetime, end_datetime
            )

    def _parse_dates(
        self, start_datetime: dt, end_datetime: dt
        ) -> pd.DatetimeIndex:
        """
        Generates a DatetimeIndex of days covering the given range.
        """
        return (
            pd.date_range(
                start_datetime.date(), end_datetime.date(), freq='d'
                )
            )

    def _aggregate_days(self, dates: pd.DatetimeIndex) -> pd.DataFrame:
        """
        Fetch the data for each item in dates.
        """
        block_data = pd.DataFrame()
        for date_ts in dates:
            date_dt = pd.to_datetime(date_ts).date()
            returned_data = self._check_data_cache(date_dt)
            if returned_data is None:
                continue

            block_data = pd.concat([block_data, returned_data])
            returned_data.drop(returned_data.index, inplace=True)
        
        return block_data

    def _load_data_from_file(self, date: dt.date()) -> pd.DataFrame:
        """
        Loads process data file for the given day.
        """
        target_file = (
            f'{self.data_folder}/{self.process_code}{date:%Y%m%d}.txt'
            )
        return ProcessData.load(target_file, self.RAW_DATA_HEADERS)
    
    def __repr__(self) -> str:
        return (f'{self.data_folder}-{self.process_code}')


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
    _process_vars: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._process_code = self.data_source.process_code

        self._process_vars = self.data_source.process_vars
        for var_, value_ in self._process_vars.items():
            self._process_vars[var_] = value_
        
        self._init_cache()

        if self.data.empty:
            raise Exception("Empty DataFrame.")

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
    def parts(self) -> pd.DataFrame:
        return self._parts

    @property
    def first_part(self) -> pd.Timestamp:
        return self._first_part

    @property
    def last_part(self) -> pd.Timestamp:
        return self._last_part

    @property
    def production_time(self) -> float:
        return self._production_time

    @property
    def part_count(self) -> int:
        return self._part_count

    @property
    def empty_cycles(self) -> pd.DataFrame:
        return self._empty_cycles

    @property
    def empty_count(self) -> int:
        return self._empty_count

    @property
    def empty_rate(self) -> float:
        return self._empty_rate

    @property
    def reworks(self) -> pd.DataFrame:
        return self._reworks

    @property
    def rework_count(self) -> int:
        return self._rework_count

    @property
    def rework_rate(self) -> float:
        return self._rework_rate

    @property
    def first_cycle(self) -> pd.Timestamp:
        return self._first_cycle

    @property
    def last_cycle(self) -> pd.Timestamp:
        return self._last_cycle

    @property
    def all_cycle_time(self) -> float:
        return self._all_cycle_time

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def cache_(self) -> dict:
        return self._cache_

    @cache_.setter
    def cache_(self, key_: Any, value_: Any) -> None:
        self._cache_[key_] = value_
    # endregion
    ...

    # region method_dicts
    def _init_cache(self) -> None:
        """
        Initializes the dictionary containing cached data
        and method calls.
        """

        self._cycle_stats_dict = {
            'first_cycle': self.first_cycle(),
            'last_cycle': self.last_cycle(),

            'all_cycle_time': self.all_cycle_time(),
            'total_cycles': self.cycle_count()
            }

        self._parts_stats_dict = {
            'parts_processed': self.part_count(),
            'first_part_processed': self.first_part(),
            'last_part_processed': self.last_part(),
            'all_production_time': self.production_time(),

            'empty_count': self.empty_count(),
            'empty_rate': self.empty_rate(),

            'rework_count': self.rework_count(),
            'rework_rate': self.rework_rate()
            }
        
        self._stops_stats_dict = {
            'total_stop_count': self.total_stop_count(),
            'total_stop_time': self.total_stop_time(),
            'total_run_time': self.total_run_time(),

            'short_stop_count': self.short_stop_count(),
            'short_stop_time': self.short_stop_time(),

            'long_stop_count': self.long_stop_count(),
            'long_stop_time': self.long_stop_time()
            }

        self._oee_stats_dict = {
            'oee_run_time': self.oee_run_time(),

            'availability_rate': self.availability_rate(),
            'performance_rate': self.performance_rate(),
            'quality_rate': self.quality_rate(),

            'oee_rate': self.oee_rate()
            }

        self._stat_dicts = {
            'cycle': self._cycle_stats_dict,
            'parts': self._parts_stats_dict,
            'stops': self._stops_stats_dict,
            'oee': self._oee_stats_dict
            }

        self._all_stats = {}
        self._cache_ = {}

        for dict_group, dict_ in self._stat_dicts.items():
            self._all_stats.update(dict_)

        for key_, method_ in self._all_stats.items():
            self.cache_[key_]['method'] = method_
    # endregion
    ...

    # region core_methods
    def _check_cache(self, key_: Any) -> Any:
        """
        Checks if the requested value has already been stored
        in local cache.
        """
        try:
            return self.cache_.get(key_).get('cache')
        except KeyError:
            value_ = self.cache_.get(key_).get('method')
            self.cache_(key_, value_)
            return self._cache_.get(key_)

    @parts.setter
    def parts(self) -> pd.DataFrame:
        """
        Returns non-empty poucher cycles for the data.
        """
        self._parts = self.data[self.data['part_present'] == 1]


    @empty_cycles.setter
    def empty_cycles(self) -> pd.DataFrame:
        """
        Returns all cycles with no part present.
        """
        self._empty_cycles = self.data[self.data['part_present'] == 0]
    # endregion
    ...

    # region all_stats
    def all_stats(self) -> None:
        self.cycle_stats()
        self.parts_stats()
        self.stops_stats()
        self.oee_stats()

    def cycle_stats(self) -> None:
        """
        Returns cycle statistics for the datablock.
        """
        for stat, method_ in self._cycle_stats_dict.items():
            self._cycle_stats_dict[stat] = method_

    def parts_stats(self) -> None:
        """
        Returns part statistics for the datablock.
        """
        for stat, method_ in self._parts_stats_dict.items():
            self._parts_stats_dict[stat] = method_

    def stops_stats(self) -> None:
        """
        Returns stop statistics for the datablock.
        """
        for stat, method_ in self._stops_stats_dict.items():
            self._stops_stats_dict[stat] = method_
    
    def oee_stats(self) -> None:
        """
        Returns OEE statistics for the data.
        """
        for stat, method_ in self._oee_stats_dict.items():
            self._oee_stats_dict[stat] = method_

    # region cycle_stats
    @first_cycle.setter
    def first_cycle(self) -> pd.Timestamp:
        """
        Returns time of first cycle for the given data.
        """
        self._first_cycle = min(self.data.index)

    @last_cycle.setter
    def last_cycle(self) -> pd.Timestamp:
        """
        Returns time of last cycle for the given data.
        """
        self._last_cycle = max(self.data.index)

    @all_cycle_time.setter
    def all_cycle_time(self) -> float:
        """
        Returns the time difference (in seconds)
        between the first and last cycle.
        """
        self._all_cycle_time = (
            self.last_cycle - self.first_cycle
            ).total_seconds()

    @cycle_count.setter
    def cycle_count(self) -> int:
        """
        Returns a cycle count for the given data.
        """
        try:
            return self._cycle_count
        except AttributeError:
            self._cycle_count = len(self.data.index)
            return self._cycle_count
    # endregion
    ...

    # region parts_stats
    @part_count.setter
    def part_count(self) -> int:
        """
        Returns the number of non-empty cycles for the data.
        """
        self._part_count = len(self.parts.index)

    @first_part.setter
    def first_part(self) -> pd.Timestamp:
        """
        Returns the DatetimeIndex of the first part made.
        """
        self._first_part = min(
            self.data[self.data['part_present']  == 1].index
            )
    
    @last_part.setter
    def last_part(self) -> pd.Timestamp:
        """
        Returns the DatetimeIndex of the last part made.
        """
        self._last_part = max(
            self.data[self.data['part_present']  == 1].index
            )

    @production_time.setter
    def production_time(self) -> float:
        """
        Returns the time difference (in seconds)
        between the first part and last part.
        """
        self._production_time = (
                self.last_part - self.first_part
            ).total_seconds()

    @empty_count.setter
    def empty_count(self) -> int:
        """
        Returns the number of empty cycles for the data.
        """
        self._empty_count = len(self.empty_cycles.index)

    @empty_rate.setter
    def empty_rate(self) -> float:
        """
        Returns the decimal percentage of empty cycles for the data.
        """
        self._empty_rate = (self.empty_count / self.cycle_count)

    @reworks.setter
    def reworks(self) -> pd.DataFrame:
        """
        Returns all cycles with duplicate serial numbers.
        """
        self._reworks = self.data[
            self.data.duplicated('serial_number')
            ]

    @rework_count.setter
    def rework_count(self) -> int:
        """
        Returns the number of parts with duplicate serial numbers.
        """
        self._rework_count = len(self.reworks.index)

    @rework_rate.setter
    def rework_rate(self) -> float:
        """
        Returns the decimal percentage of reworked parts.
        """
        self._rework_rate = (self.rework_count / self.cycle_count)
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
                self.data[self.data['cycle_time']
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
                self.data[self.data['cycle_time']
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
                self.data[self.data['cycle_time']
                > self.SHORT_STOP_LIMIT],
                self.data[self.data['cycle_time']
                < self.MAX_CYCLE_TIME]
            ]).index
            self._short_stops = self.data.drop(drop_rows).dropna()
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
            drop_rows = self.data[
                self.data['cycle_time'] < self.SHORT_STOP_LIMIT
                ].index
            self._long_stops = self.data.drop(drop_rows).dropna()
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
                self._start_datetime, self._end_datetime, freq=freq
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
            np.arange(range_size)* self.STANDARD_RATE_PER_S
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
            self.data['part_count'] = self.data['part_present'].cumsum()
        except Exception:
            pass
        finally:
            return self.data['part_count']
    # endregion
    ...

    def __repr__(self) -> str:
        return (
            f'{self._source}_{self._start_datetime:%Y%m%d-%H%M%S}_'
            f'{self._end_datetime:%Y%m%d-%H%M%S}'
        )