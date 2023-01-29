from __future__ import annotations

import math
from datetime import date
from datetime import datetime as dt
from datetime import time, timedelta

import pandas as pd

from application import db
from application.models import WorkOrders, WorkWeeks

def update_work_order(work_order: WorkOrders, hours: pd.Series) -> None:
    work_order.remaining_qty = work_order.strip_qty - work_order.pouched_qty
    work_order.remaining_time = (
        math.ceil(
            work_order.remaining_qty / work_order.standard_rate
            )
        )
    

class Schedule:
    """Schedule for a single production week.

    Returns:
        Instance of Schedule class.
    """
    _year_week_format = '%G-%V'

    def __init__(self: Schedule, year_week: str) -> None:
        self.year_week = year_week
        self._init_week()
        self._init_dates()
        self._init_frames()
        
    def _init_week(self) -> None:
        """Initializes database info for the week.
        """
        self._week = self._get_work_week()
        self._week_config()
        
    def _get_work_week(self: Schedule) -> WorkWeeks:
        week_ = WorkWeeks.query.filter(
            WorkWeeks.year_week == self.year_week
            ).first()
        if week_ is None:
            week_ = WorkWeeks(
                year_week=self.year_week,  
            )
            db.session.add(week_)
            db.session.commit()
        return week_
    
    def _week_config(self: Schedule) -> None:
        self._production_days = self._get_days()
        self.workday_start = time(self._week.workday_start_time)
        self.workday_end = time(self._week.workday_end_time)
        self.lines = self._get_lines()
        
    def _get_days(self: Schedule) -> list[int]:
        """Returns a list of integers representing the days scheduled
        for the given week. 

        Returns:
            list[int]: List of days scheduled. 0 = Monday, 6 = Sunday.
        """
        bin_list_str = list(bin(self._week.prod_days))[2:]
        bin_list_int = list(map(int, bin_list_str))

        days = range(7) # 0 - 6
        _days = []

        for day, scheduled in zip(days, bin_list_int):
            if scheduled:
                _days.append(day) 
        return _days
        
    def _get_lines(self: Schedule) -> list[int]:
        """Returns list of integers representing the lines (5-12)
        in production for the given week.

        Returns:
            list[int]: Line numbers available for production.
        """
        bin_list_str = list(bin(self._week.lines))[2:]
        bin_list_int = list(map(int, bin_list_str))
        
        lines = range(5, 13) # 5 - 12
        _lines = []

        for line, scheduled in zip(lines, bin_list_int):
            if scheduled:
                _lines.append(line)
        return _lines

    def _init_dates(self: Schedule) -> None:
        self.start_datetime = dt.strptime(
            f'{self.year_week}-Mon',
            f'{Schedule._year_week_format}-%a'
            )
        self.end_date = self.start_datetime + timedelta(days=6)
        self.end_datetime = dt.combine(self.end_date, time().max)
        self.dates = pd.date_range(
            self.start_datetime, self.end_datetime,
            freq='d'
            )
        self._set_schedule_type()

    def _set_schedule_type(self: Schedule) -> None:
        if self.start_datetime < dt.now() < self.end_datetime:
            self.schedule_type = 'current'
        elif self.end_datetime < dt.now():
            self.schedule_type = 'past'
        elif self.start_datetime > dt.now():
            self.schedule_type = 'future'
        else:
            raise Exception('Error setting week type (Current/Past/Future).')

    def _init_frames(self: Schedule) -> None:
        """Builds a pandas DataFrame for the given schedule.
        """
        week_frame_index = pd.date_range(
            start=self.start_datetime, end=self.end_datetime, freq='h'
            )
        self._week_frame = pd.DataFrame(
            columns=self.lines, index=week_frame_index
            )
        self._week_frame['scheduled'] = False
        self._update_frames()

    def _update_frames(self: Schedule) -> None:
        self._update_hours()
        self._update_schedule_frame()
        self._update_work_orders()
        for work_order in self.work_orders:
            self._map_work_order(work_order)

    def set_hours(self: Schedule, workday_start: int, workday_end: int) -> None:
        self._week.workday_start_time = time(workday_start)
        self._week.workday_end_time = time(workday_end)
        db.session.commit()
        self._init_week()
        self._update_frames()
        
    def set_days(self: Schedule, days: int) -> None:
        self._week.prod_days = days
        db.session.commit()
        self._init_week()
        self._update_frames()

    def _update_hours(self: Schedule) -> None:
        self._week_frame.loc[
            self.workday_start:self.workday_end.replace(
                hour=self.workday_end.hour - 1
                ), 'scheduled'
            ] = True

        day_mask = pd.Series(False, index=self._week_frame.index)
        for _day in self._production_days:
            day_mask[day_mask.index.to_series().dt.weekday == _day] = True

        self.hours = self._week_frame['scheduled'] & day_mask
        
    def _update_schedule_frame(self: Schedule) -> None:
        self._schedule_frame = pd.DataFrame(
            index=self.hours.index[self.hours == True],
            columns=self.lines
            )

    def _update_work_orders(self: Schedule) -> None:
        self._fetch_work_orders()
        for work_order in self.work_orders:
            if work_order.status == 'Pouching':
                update_work_order(work_order, self.hours)
            if work_order.status == 'Queued':
                pass # update queued work orders start/completion times
        
    def _fetch_work_orders(self: Schedule) -> None:
        self.work_orders = WorkOrders.query.filter(
                WorkOrders.end_datetime >= self.start_datetime
            ).filter(
                WorkOrders.start_datetime <= self.end_datetime
            ).order_by(WorkOrders.start_datetime.desc()).all()

    def _map_work_order(self: Schedule, work_order: WorkOrders) -> None:
        pass # map work orders to css grid values
    
    

    @property
    def prior_week(self: Schedule) -> str:
        try:
            return self._prior_year_week
        except AttributeError:
            prior_week_start = self.start_datetime - timedelta(days=7)
            self._prior_year_week = dt.strftime(
                prior_week_start, Schedule._year_week_format
                )
            return self._prior_year_week

    @property
    def next_week(self: Schedule) -> str:
        try:
            return self._next_year_week
        except AttributeError:
            next_week_start = self.start_datetime + timedelta(days=7)
            self._next_year_week = dt.strftime(
                next_week_start, Schedule._year_week_format
                )
            return self._next_year_week

    @staticmethod
    def parking_lot() -> list[WorkOrders]:
        """
        Returns database query for all 'Parking Lot' jobs.
        """
        return (
            WorkOrders.query.filter(
                WorkOrders.status == 'Parking Lot'
                ).order_by(WorkOrders.add_datetime.desc()).all()
            )

    @staticmethod
    def grid_hour(datetime_: dt) -> int:
        """
        Returns integer representing the grid column for the
        given datetime hour. Ranges from 0 - 167, with 0 representing
        12AM - 1AM Monday morning.
        """
        return (datetime_.weekday() * 24) + datetime_.hour

    def __str__(self: Schedule) -> str:
        return (
            f'{self.start_datetime:%b %d, %Y} - '
            f'{self.end_datetime:%b %d, %Y}'
            )


class CurrentSchedule(Schedule):

    def __init__(self: CurrentSchedule) -> None:
        year_week = dt.strftime(dt.now(), Schedule._year_week_format)
        super().__init__(year_week=year_week)

    def current_hour(self: CurrentSchedule) -> int:
        return self.grid_hour(dt.now())