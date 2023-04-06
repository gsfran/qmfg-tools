from __future__ import annotations

import math
from datetime import datetime as dt
from datetime import time, timedelta

import pandas as pd
from sqlalchemy import and_, or_

from application import db
from application.machines import machines
from application.models import WorkOrder, WorkWeek


def current_hour() -> dt:
    return dt.now().replace(minute=0, second=0, microsecond=0)


def _crop_frame(_schedule_frame: pd.DataFrame, line: int) -> pd.Series:
    _frame = _schedule_frame.loc[current_hour():, line]
    return _frame


def _multi_week_frame() -> pd.DataFrame:
    _next_week_obj = Schedule(CurrentSchedule().next_week)
    _multi = pd.concat(
        [CurrentSchedule().schedule_frame, _next_week_obj.schedule_frame]
    )
    _frame_after_next = Schedule(_next_week_obj.next_week).schedule_frame
    _multi = pd.concat([_multi, _frame_after_next])
    return _multi


def map_work_order(
    work_order: WorkOrder, _frame: pd.Series[str]
) -> pd.Series[str]:
    work_order.remaining_qty = work_order.strip_qty - work_order.pouched_qty
    work_order.remaining_time = math.ceil(
        work_order.remaining_qty / work_order.standard_rate
    )
    wo_start = get_first_hour(_frame)
    wo_end = get_last_hour(_frame, work_order)

    if work_order.status == 'Queued':
        work_order.start_datetime = wo_start

    work_order.end_datetime = wo_end

    db.session.commit()

    _frame[wo_start:wo_end] = work_order.pouch_lot_num
    return _frame


def get_first_hour(_frame: pd.Series[str]) -> dt:
    return _frame.isna().first_valid_index().to_pydatetime()  # type: ignore


def get_last_hour(_frame: pd.Series[str], work_order: WorkOrder) -> dt | None:
    if work_order.status == 'Pouching':
        return _frame[dt.now():].head(
            work_order.remaining_time
        ).isna().last_valid_index().to_pydatetime()  # type: ignore

    elif work_order.status == 'Queued':
        return _frame[work_order.start_datetime:].head(
            work_order.remaining_time
        ).isna().last_valid_index().to_pydatetime()  # type: ignore

    else:
        return None


class Schedule:
    """Schedule for a single production week.

    Returns:
        Instance of Schedule class.
    """
    _year_week_format = '%G-%V'

    def __init__(self: Schedule, year_week: str, mach_type: str) -> None:
        self.year_week = year_week
        self.mach_type = mach_type
        self._init_week()

    def _init_week(self) -> None:
        self.work_week = self._get_work_week()
        self._week_config()
        self._init_dates()

    def _get_work_week(self: Schedule) -> WorkWeek:
        work_week = db.session.execute(
            db.select(WorkWeek).where(
                WorkWeek.year_week == self.year_week
            )
        ).scalar_one_or_none()
        if work_week is None:
            work_week = WorkWeek(year_week=self.year_week)
            db.session.add(work_week)
            db.session.commit()
        return work_week

    def _week_config(self: Schedule) -> None:
        self._production_days = self._parse_days()
        self.machines = self._init_machines()

    def _parse_days(self: Schedule) -> list[int]:
        """Returns a list of integers representing the days scheduled
        for the given week.

        Returns:
            list[int]: List of days scheduled. 0 = Monday, 6 = Sunday.
        """
        
        #  need to figure out how to handle/store/load default schedule config

        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        weekday_nums = range(7)
        scheduled_days = []
        
        columns_to_check = [f'{day}_start_time' for day in days]

        for column, weekday_num in zip(columns_to_check, weekday_nums):
            scheduled = self.work_week.__getattribute__(column)
            if scheduled:
                scheduled_days.append(weekday_num)
        return scheduled_days

    def _init_machines(self: Schedule) -> list[int]:
        """Returns list of integers representing the machines
        in production for the given week.

        Returns:
            list[int]: Line numbers available for production.
        """

        lines =
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

    def set_hours(self: Schedule, start: int, end: int) -> None:
        self.work_week.workday_start_time = time(start)
        self.work_week.workday_end_time = time(end)
        db.session.commit()
        self.reload()

    def set_days(self: Schedule, days: int) -> None:
        self.work_week.prod_days = days
        db.session.commit()
        self.reload()

    @property
    def _index(self: Schedule) -> pd.DatetimeIndex:
        try:
            return self.index_
        except AttributeError:
            self.index_ = pd.date_range(
                start=self.start_datetime, end=self.end_datetime, freq='h'
            )
            return self.index_

    @property
    def schedule_frame(self: Schedule) -> pd.DataFrame:
        try:
            return self._schedule_frame
        except AttributeError:
            self._schedule_frame = pd.DataFrame(
                index=self.hours.index[self.hours],
                columns=self.machines
            )
            return self._schedule_frame

    @property
    def hours(self: Schedule) -> pd.Series:
        try:
            return self._hours
        except AttributeError:
            self.hour_mask
            self.day_mask
            self._hours = self._day_mask & self._hour_mask
            return self._hours

    @property
    def hour_mask(self: Schedule) -> pd.Series:
        try:
            return self._hour_mask
        except AttributeError:
            self._hour_mask = pd.Series(False, index=self._index)
            last_hour = self.workday_end.replace(
                hour=self.workday_end.hour-1
            )
            self._hour_mask[self.workday_start:last_hour] = True
            return self._hour_mask

    @property
    def day_mask(self: Schedule) -> pd.Series:
        try:
            return self._day_mask
        except AttributeError:
            self._day_mask = pd.Series(False, index=self._index)
            for _day in self._production_days:
                self._day_mask[
                    self._index.to_series().dt.weekday == _day
                ] = True
            return self._day_mask

    @property
    def work_orders(self: Schedule) -> list[WorkOrder]:
        def _get_work_orders() -> list[WorkOrder]:
            return db.session.execute(db.select(WorkOrder).where(
                and_(
                    WorkOrder.end_datetime >= self.start_datetime,
                    WorkOrder.start_datetime < self.end_datetime
                )
            ).order_by(WorkOrder.start_datetime.desc())).scalars()
        try:
            return self._work_orders
        except AttributeError:
            self._work_orders = _get_work_orders()
            return self._work_orders

    def _map_work_order(self: Schedule, work_order: WorkOrder) -> None:
        pass  # map work orders to css grid values

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

    def reload(self: Schedule) -> None:
        self.__init__(self.year_week)

    @staticmethod
    def refresh() -> None:
        _frame = _multi_week_frame()
        for work_order in Schedule.scheduled_jobs():
            line = work_order.line
            cropped_frame = _crop_frame(_frame, line)
            cropped_frame = map_work_order(
                work_order=work_order, _frame=cropped_frame
            )
            _frame[line] = cropped_frame

    @staticmethod
    def parking_lot() -> list[WorkOrder]:
        """
        Returns database query for all 'Parking Lot' jobs.
        """
        return db.session.execute(
            db.select(WorkOrder).where(
                WorkOrder.status == 'Parking Lot'
            ).order_by(
                WorkOrder.add_datetime.desc()
            )
        ).scalars()

    @staticmethod
    def pouching() -> list[WorkOrder]:
        """
        Returns database query for all 'Pouching' jobs.
        """
        return db.session.execute(
            db.select(WorkOrder).where(
                WorkOrder.status == 'Pouching'
            ).order_by(
                WorkOrder.line
            )
        ).scalars()

    @staticmethod
    def queued() -> list[WorkOrder]:
        """Returns db query for all Queued jobs.

        Returns:
            list[WorkOrders]: Scheduled work orders.
        """
        return db.session.execute(
            db.select(WorkOrder).where(
                WorkOrder.status == 'Queued'
            ).order_by(
                WorkOrder.line
            )
        ).scalars()

    @staticmethod
    def scheduled_jobs() -> list[WorkOrder]:
        """Returns db query for all Pouching and Queued jobs.

        Returns:
            list[WorkOrders]: Scheduled work orders.
        """
        return db.session.execute(
            db.select(WorkOrder).where(
                or_(
                    WorkOrder.status == 'Pouching',
                    WorkOrder.status == 'Queued'
                )
            )
        ).scalars()

    @staticmethod
    def on_line(line: str | None) -> WorkOrder | None:
        return db.session.execute(
            db.select(WorkOrder).where(
                and_(
                    WorkOrder.line == line,
                    WorkOrder.status == 'Pouching'
                )
            )
        ).scalar_one_or_none()

    @staticmethod
    def week_hour(datetime_: dt) -> int:
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

    def __init__(self: CurrentSchedule, mach_type: str) -> None:
        year_week = dt.strftime(dt.now(), Schedule._year_week_format)
        super().__init__(year_week=year_week, mach_type=mach_type)

    @property
    def current_week_hour(self: CurrentSchedule) -> int:
        self._current_week_hour = self.week_hour(dt.now())
        return self._current_week_hour

    @property
    def current_hour(self: CurrentSchedule) -> dt:
        return current_hour()
