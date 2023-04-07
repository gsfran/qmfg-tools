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


def _three_week_frame() -> pd.DataFrame:
    _next_week_obj = PouchingSchedule(
        year_week=CurrentPouchingSchedule().next_week)
    _three_week_frame = pd.concat(
        [CurrentPouchingSchedule().schedule_frame,
         _next_week_obj.schedule_frame]
    )

    _week_after_next_obj = PouchingSchedule(
        year_week=_next_week_obj.next_week)

    _three_week_frame = pd.concat(
        [_three_week_frame, _week_after_next_obj.schedule_frame]
    )

    return _three_week_frame


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


class PouchingSchedule:
    """Schedule for pouching that covers a single production week.

    Returns:
        Instance of Schedule class.
    """
    _year_week_format = '%G-%V'

    def __init__(self: PouchingSchedule, year_week: str) -> None:
        self.year_week = year_week
        self._init_week()

    def _init_week(self) -> None:
        self.work_week = self._get_work_week()
        self._week_config()
        self._get_dates()

    def _get_work_week(self: PouchingSchedule) -> WorkWeek:
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

    def _week_config(self: PouchingSchedule) -> None:
        self.production_days = self._init_weekdays()
        self.active_machines = self._init_machines()

    def _init_weekdays(self: PouchingSchedule) -> list[int]:
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
            if scheduled is not None:
                scheduled_days.append(weekday_num)
        return scheduled_days

    def _init_machines(self: PouchingSchedule) -> list[int]:
        """Returns list of integers representing the machines
        in production for the given week.

        Returns:
            list[int]: Line numbers available for production.
        """
        _machine_list = []
        for mach_type in machines.keys():
            if mach_type != 'itrak':
                break
            for machine_id in machines[mach_type]:
                _machine_list.append(f'{mach_type}_{machine_id}')

        _active_machines = []

        for _machine in _machine_list:
            scheduled = self.work_week.__getattribute__(_machine)
            if scheduled:
                _active_machines.append(_machine)
        return _active_machines

    def _get_dates(self: PouchingSchedule) -> None:
        self.start_datetime = dt.strptime(
            f'{self.year_week}-Mon',
            f'{PouchingSchedule._year_week_format}-%a'
        )
        self.end_date = self.start_datetime + timedelta(days=6)
        self.end_datetime = dt.combine(self.end_date, time().max)
        self.dates = pd.date_range(
            self.start_datetime, self.end_datetime,
            freq='d'
        )
        self._set_schedule_type()

    def _set_schedule_type(self: PouchingSchedule) -> None:
        if self.start_datetime < dt.now() < self.end_datetime:
            self.schedule_type = 'current'
        elif self.end_datetime < dt.now():
            self.schedule_type = 'past'
        elif self.start_datetime > dt.now():
            self.schedule_type = 'future'
        else:
            raise Exception('Error setting week type (Current/Past/Future).')

    def set_hours(self: PouchingSchedule, start: int, end: int) -> None:
        self.work_week.workday_start_time = time(start)
        self.work_week.workday_end_time = time(end)
        db.session.commit()
        self.reload()

    def set_days(self: PouchingSchedule, days: int) -> None:
        self.work_week.prod_days = days
        db.session.commit()
        self.reload()

    @property
    def _index(self: PouchingSchedule) -> pd.DatetimeIndex:
        try:
            return self.index_
        except AttributeError:
            self.index_ = pd.date_range(
                start=self.start_datetime, end=self.end_datetime, freq='h'
            )
            return self.index_

    @property
    def schedule_frame(self: PouchingSchedule) -> pd.DataFrame:
        try:
            return self._schedule_frame
        except AttributeError:
            self._schedule_frame = pd.DataFrame(
                index=self.hours.index[self.hours],
                columns=self.active_machines
            )
            return self._schedule_frame

    @property
    def hours(self: PouchingSchedule) -> pd.Series:
        try:
            return self._hours
        except AttributeError:
            self.hour_mask
            self.day_mask
            self._hours = self._day_mask & self._hour_mask
            return self._hours

    @property
    def hour_mask(self: PouchingSchedule) -> pd.Series:
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
    def day_mask(self: PouchingSchedule) -> pd.Series:
        try:
            return self._day_mask
        except AttributeError:
            self._day_mask = pd.Series(False, index=self._index)
            for _day in self.production_days:
                self._day_mask[
                    self._index.to_series().dt.weekday == _day
                ] = True
            return self._day_mask

    @property
    def work_orders(self: PouchingSchedule) -> list[WorkOrder]:
        def _get_work_orders() -> list[WorkOrder]:
            return db.session.execute(
                db.select(WorkOrder).where(
                    and_(
                        WorkOrder.end_datetime >= self.start_datetime,
                        WorkOrder.start_datetime < self.end_datetime
                    )
                ).order_by(
                    WorkOrder.start_datetime.desc()
                )
            ).scalars()
        try:
            return self._work_orders
        except AttributeError:
            self._work_orders = _get_work_orders()
            return self._work_orders

    def _map_work_order(self: PouchingSchedule, work_order: WorkOrder) -> None:
        pass  # map work orders to css grid values

    @property
    def prior_week(self: PouchingSchedule) -> str:
        try:
            return self._prior_year_week
        except AttributeError:
            prior_week_start = self.start_datetime - timedelta(days=7)
            self._prior_year_week = dt.strftime(
                prior_week_start, PouchingSchedule._year_week_format
            )
            return self._prior_year_week

    @property
    def next_week(self: PouchingSchedule) -> str:
        try:
            return self._next_year_week
        except AttributeError:
            next_week_start = self.start_datetime + timedelta(days=7)
            self._next_year_week = dt.strftime(
                next_week_start, PouchingSchedule._year_week_format
            )
            return self._next_year_week

    def reload(self: PouchingSchedule) -> None:
        self.__init__(year_week=self.year_week)

    @staticmethod
    def refresh() -> None:
        _frame = _three_week_frame()
        for work_order in PouchingSchedule.scheduled_jobs():
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

    def __str__(self: PouchingSchedule) -> str:
        return (
            f'{self.start_datetime:%b %d, %Y} - '
            f'{self.end_datetime:%b %d, %Y}'
        )


class CurrentPouchingSchedule(PouchingSchedule):

    def __init__(self: CurrentPouchingSchedule) -> None:
        year_week = dt.strftime(dt.now(), PouchingSchedule._year_week_format)
        super().__init__(year_week=year_week)

    @property
    def current_week_hour(self: CurrentPouchingSchedule) -> int:
        self._current_week_hour = self.week_hour(dt.now())
        return self._current_week_hour

    @property
    def current_hour(self: CurrentPouchingSchedule) -> dt:
        return current_hour()
