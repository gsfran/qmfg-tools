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
    def cached_data(self) -> dict:
        return self._cached_data

    def store_cached_data(self, key_: dt, data: pd.DataFrame) -> None:
        self._cached_data.update({key_: data})

    def load_data(self, key_: dt) -> pd.DataFrame:
        """
        Returns cached data if it exists, otherwise loads 
        the data from process data files.
        """
        try:    
            return self.cached_data[key_]
        except KeyError:
            data = self._load_data_from_file(key_)
        
        self.store_cached_data(key_, data)
        return self.cached_data[key_]
    # endregion
    ...

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
                start_datetime, end_datetime, freq='d'
                )
            )

    def _aggregate_days(self, days: pd.DatetimeIndex) -> pd.DataFrame:
        """
        Fetch the data for each item in dates.
        """
        block_data = pd.DataFrame()
        for day in days.to_pydatetime():
            returned_data = self.load_data(day)
            if returned_data is None:
                print('No data read.')
                continue
            
            self.store_cached_data(day, returned_data)
            block_data = pd.concat([block_data, returned_data])
            returned_data.drop(returned_data.index, inplace=True)
        
        return block_data

    def _load_data_from_file(self, date: dt) -> pd.DataFrame:
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
    
    def __post_init__(self) -> None:
        if self.data.empty:
            raise Exception("Empty DataFrame.")
        
        self._process_code = self.data_source.process_code
        self._process_vars = self.data_source.process_vars

        for var_, value_ in self._process_vars.items():
            self._process_vars[var_] = value_


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
        
        return self.parts

    @property
    def first_part(self) -> pd.Timestamp:
        """
        Returns the DatetimeIndex of the first part made.
        """
        try:
            return self._first_part
        except AttributeError:
            self._first_part = min(
                self.data[self.data['part_present']  == 1].index
                )
        
        return self.first_part

    @property
    def last_part(self) -> pd.Timestamp:
        """
        Returns the DatetimeIndex of the last part made.
        """
        try:
            return self._last_part
        except AttributeError:
            self._last_part = max(
                self.data[self.data['part_present']  == 1].index
                )
        
        return self.last_part

    @property
    def production_time(self) -> float:
        """
        Returns the time difference (in seconds)
        between the first part and last part.
        """
        try:
            return self._production_time
        except AttributeError:
            self._production_time = (
                self.last_part - self.first_part
            ).total_seconds()
        
        return self.production_time

    @property
    def part_count(self) -> int:
        """
        Returns the number of non-empty cycles for the data.
        """
        try:
            return self._part_count
        except AttributeError:
            self._part_count = len(self.parts.index)

        return self.part_count

    @property
    def empty_cycles(self) -> pd.DataFrame:
        """
        Returns all cycles with no part present.
        """
        try:
            return self._empty_cycles
        except AttributeError:
            self._empty_cycles = self.data[self.data['part_present'] == 0]

        return self.empty_cycles

    @property
    def empty_count(self) -> int:
        """
        Returns the number of empty cycles for the data.
        """
        try:
            return self._empty_count
        except AttributeError:
            self._empty_count = len(self.empty_cycles.index)

        return self.empty_count

    @property
    def empty_rate(self) -> float:
        """
        Returns the decimal percentage of empty cycles for the data.
        """
        try:
            return self._empty_rate
        except AttributeError:
            self._empty_rate = (self.empty_count / self.cycle_count)

        return self.empty_rate
            
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

        return self.reworks

    @property
    def rework_count(self) -> int:
        """
        Returns the number of parts with duplicate serial numbers.
        """
        try:
            return self._rework_count
        except AttributeError:
            self._rework_count = len(self.reworks.index)

        return self.rework_count

    @property
    def rework_rate(self) -> float:
        """
        Returns the decimal percentage of reworked parts.
        """
        try:
            return self._rework_rate
        except AttributeError:
            self._rework_rate = (self.rework_count / self.cycle_count)

        return self.rework_rate
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
                > self.process_vars['MAX_CYCLE_TIME']]
            )

        return self.stops

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
                < self.process_vars['MAX_CYCLE_TIME']]
            )
        
        return self.run_cycles

    @property
    def total_stop_count(self) -> int:
        """
        Returns the number of stops for the given data.
        """
        try:
            return self._total_stop_count
        except AttributeError:
            self._total_stop_count = len(self.stops.index)
        
        return self.total_stop_count

    @property
    def total_stop_time(self) -> float:
        """
        Returns the sum of cycle times greater than the maximum.
        """
        try:
            return self._total_stop_time
        except AttributeError:
            self._total_stop_time = sum(self.stops['cycle_time'])
        
        return self.total_stop_time

    @property
    def total_run_time(self) -> float:
        """
        Returns the sum of cycle times less than the maximum.
        """
        try:
            return self._total_run_time
        except AttributeError:
            self._total_run_time = sum(self.run_cycles['cycle_time'])
        
        return self.total_run_time

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
        
        return self.uptime_percentage

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
                > self.process_vars['SHORT_STOP_LIMIT']],
                self.data[self.data['cycle_time']
                < self.process_vars['MAX_CYCLE_TIME']]
            ]).index
            self._short_stops = self.data.drop(drop_rows).dropna()
        
        return self.short_stops

    @property
    def short_stop_count(self) -> int:
        """
        Returns the number of short stops for the data.
        """
        try:
            return self._short_stop_count
        except AttributeError:
            self._short_stop_count = len(self.short_stops.index)
        
        return self.short_stop_count

    @property
    def short_stop_time(self) -> float:
        """
        Returns the total time in seconds of all short stops.
        """
        try:
            return self._short_stop_time
        except AttributeError:
            self._short_stop_time = sum(self.short_stops['cycle_time'])
        
        return self.short_stop_time

    @property
    def long_stops(self) -> pd.DataFrame:
        """
        Returns all stops with duration longer than SHORT_STOP_LIMIT.
        """
        try:
            return self._long_stops
        except AttributeError:
            drop_rows = self.data[
                self.data['cycle_time'] < self.process_vars['SHORT_STOP_LIMIT']
                ].index
            self._long_stops = self.data.drop(drop_rows).dropna()
        
        return self.long_stops
    
    @property
    def long_stop_count(self) -> int:
        """
        Returns the number of long stops for the data.
        """
        try:
            return self._long_stop_count
        except AttributeError:
            self._long_stop_count = len(self.long_stops.index)
        
        return self.long_stop_count

    @property
    def long_stop_time(self) -> float:
        """
        Returns the total time in seconds of all long stops.
        """
        try:
            return self._long_stop_time
        except AttributeError:
            self._long_stop_time = sum(self.long_stops['cycle_time'])
    
        return self.long_stop_time
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
            self._oee_run_time = (
                self.total_run_time + self.short_stop_time
            )
        
        return self.oee_run_time

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
                / (self.process_vars['IDEAL_RATE_PER_S'] / 60)
            )
        
        return self.performance_rate

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
            self._quality_rate = (
                1 - (self.rework_count / self.part_count)
            )
        
        return self.quality_rate

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
        
        return self.oee_rate
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
            f'{self._data_source}_{self._start_datetime:%Y%m%d-%H%M%S}_'
            f'{self._end_datetime:%Y%m%d-%H%M%S}'
        )