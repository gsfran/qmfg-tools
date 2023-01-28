from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from datetime import datetime as dt
from datetime import time, timedelta

import pandas as pd

from application import db
from application.models import WorkOrders


@dataclass
class Schedule:
    """Schedule for a single production week.

    Returns:
        Instance of Schedule class.
    """
    year_week: str
    workday_start: time = time(6)
    workday_end: time = time(22)
    non_production_days: list = field(default_factory=list)

    _year_week_format = '%G-%V'

    def __post_init__(self) -> None:
        self.lines = range(5, 10)
        self.non_production_days = [5, 6] # Sat Sun
        self._build_dates()
        self._init_frame()

    def _init_frame(self) -> None:
        """Builds a pandas DataFrame for the given schedule.
        """
        dt_index = pd.date_range(
            start=self.start_datetime, end=self.end_datetime, freq='h'
            )
        self._schedule_frame = pd.DataFrame(columns=self.lines, index=dt_index)
        self._schedule_frame['scheduled'] = False
        self._update_frame()
        print(self._schedule_frame)

    def _update_frame(self) -> None:
        self._refresh_sched_hours()
        self._refresh_work_orders()
        for work_order in self.work_orders:
            self._map_work_order(work_order)

    def update_hours(self, workday_start: time, workday_end: time) -> None:
        self.workday_start = workday_start
        self.workday_end = workday_end

    def _refresh_sched_hours(self) -> None:
        self._schedule_frame['scheduled'].loc[self.workday_start:self.workday_end,
            ] = True
        # for _day in self.non_production_days:
        #     self._schedule_frame['scheduled'].loc[
        #         self._schedule_frame.index.to_series().dt.weekday == _day
        #         ] = False
        self.scheduled_hours = self._schedule_frame['scheduled']

    def _refresh_work_orders(self) -> None:
        self.work_orders = WorkOrders.query.filter(
                WorkOrders.end_datetime >= self.start_datetime
            ).filter(
                WorkOrders.start_datetime <= self.end_datetime
            ).order_by(WorkOrders.start_datetime.desc()).all()

    def _map_work_order(self, work_order: WorkOrders) -> None:
        if work_order.start_datetime < self.start_datetime:
            work_order._start = self.grid_hour(work_order.start_datetime)
            work_order._end = self.grid_hour(work_order.end_datetime)

    def _build_dates(self) -> None:
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

    def _set_schedule_type(self) -> None:
        if self.start_datetime < dt.now() < self.end_datetime:
            self.schedule_type = 'current'
        elif self.end_datetime < dt.now():
            self.schedule_type = 'past'
        elif self.start_datetime > dt.now():
            self.schedule_type = 'future'
        else:
            raise Exception('Error setting week type (Current/Past/Future).')

    def is_this_week(self, datetime_: dt) -> bool:
        if dt.strftime(
            datetime_, Schedule._year_week_format
            ) == self.year_week:
            return True
        return False

    @property
    def prior_week(self) -> str:
        try:
            return self._prior_year_week
        except AttributeError:
            prior_week_start = self.start_datetime - timedelta(days=7)
            self._prior_year_week = dt.strftime(
                prior_week_start, Schedule._year_week_format
                )
            return self._prior_year_week

    @property
    def next_week(self) -> str:
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

    def __str__(self):
        return (
            f'{self.start_datetime:%b %d, %Y} - '
            f'{self.end_datetime:%b %d, %Y}'
            )


class CurrentSchedule(Schedule):

    def __init__(self) -> None:
        year_week = dt.strftime(dt.now(), Schedule._year_week_format)
        super().__init__(year_week=year_week)

    def current_hour(self) -> int:
        return self.grid_hour(dt.now())