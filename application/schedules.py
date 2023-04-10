from __future__ import annotations

import json
import math
import os
from datetime import date
from datetime import datetime as dt
from datetime import time, timedelta

import pandas as pd
from sqlalchemy import and_, or_

from application import db
from application.machines import machines
from application.models import WorkOrder, WorkWeek

_YEAR_WEEK_FORMAT = '%G-%V'

_WEEKDAY_TAGS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

_WEEKDAY_START_TIME_COLS = [
    f'{weekday_}_start_time' for weekday_ in _WEEKDAY_TAGS
]


with open(os.environ['SCHEDULE_JSON'], 'r') as schedule_json:
    schedule_times: dict[str, str] = json.load(schedule_json)


def current_hour() -> dt:
    return dt.now().replace(minute=0, second=0, microsecond=0)


def create_week(year_week: str) -> WorkWeek:
    print(f'Creating week {year_week}')
    work_week = WorkWeek(year_week=year_week)
    for day_attr, time_ in schedule_times.items():
        print(time_)
        if time_ is not None:
            work_week.__setattr__(day_attr, dt.strptime(time_, '%H:%M').time())
    for machine_, active_ in machines.items():
        work_week.__setattr__(machine_, active_)
    db.session.add(work_week)
    db.session.commit()
    return work_week


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
        Instance of PouchingSchedule class.
    """

    def __init__(self: PouchingSchedule, year_week: str) -> None:
        self.year_week = year_week
        self._init_schedule()

    def _init_schedule(self) -> None:
        self.dates
        self.schedule_tense
        self.work_week = self._get_work_week_from_db()
        self.scheduled_days = self._get_scheduled_days_from_db()
        self.active_machines = self._get_active_machines_from_db()

    def _get_work_week_from_db(self: PouchingSchedule) -> WorkWeek:
        work_week: WorkWeek = db.session.execute(
            db.select(WorkWeek).where(
                WorkWeek.year_week == self.year_week
            )
        ).scalar_one_or_none()
        if work_week is None:
            work_week = create_week(year_week=self.year_week)
        return work_week

    def _get_scheduled_days_from_db(self: PouchingSchedule) -> list[date]:
        """Returns a list of datetime.date objects representing
        the days scheduled for the given week.

        Returns:
            list[str]: List of days scheduled for the week.
        """
        scheduled_days: list[date] = []
        for weekday_num, column in enumerate(_WEEKDAY_START_TIME_COLS):
            scheduled = self.work_week.__getattribute__(column)
            if scheduled is None:
                continue
            date_ = self.dates[weekday_num].date()
            scheduled_days.append(date_)
        return scheduled_days

    def _get_active_machines_from_db(self: PouchingSchedule) -> list[str]:
        """Returns list of strings representing the machines
        in production for the given week.

        Returns:
            list[str]: Machines available for production.
        """
        machine_list: list[str] = []
        for machine_ in machines.keys():
            machine_list.append(f'{machine_}')

        active_machines: list[str] = []
        for machine_ in machine_list:
            scheduled = self.work_week.__getattribute__(machine_)
            if scheduled:
                active_machines.append(machine_)
        return active_machines

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
    def dates(self: PouchingSchedule) -> pd.DatetimeIndex:
        try:
            return self._dates
        except AttributeError:
            self.start_datetime = dt.strptime(
                f'{self.year_week}-Mon', f'{_YEAR_WEEK_FORMAT}-%a'
            )
            self.end_date = self.start_datetime + timedelta(days=6)
            self.end_datetime = dt.combine(self.end_date, time().max)
            self._dates = pd.date_range(
                self.start_datetime,
                self.end_datetime,
                freq='d'
            )
            return self._dates

    @property
    def schedule_tense(self: PouchingSchedule) -> str:
        try:
            return self._schedule_tense
        except AttributeError:
            if self.start_datetime < dt.now() < self.end_datetime:
                self._schedule_tense = 'current'
            elif self.end_datetime < dt.now():
                self._schedule_tense = 'past'
            elif self.start_datetime > dt.now():
                self._schedule_tense = 'future'
            else:
                raise Exception(
                    'Error encountered while determining week tense.'
                )
            return self._schedule_tense

    @property
    def index_(self: PouchingSchedule) -> pd.DatetimeIndex:
        try:
            return self._frame_index
        except AttributeError:
            self._frame_index = pd.date_range(
                start=self.start_datetime,
                end=self.end_datetime,
                freq='30min'
            )
            return self._frame_index

    @property
    def index_freq(self: PouchingSchedule) -> str | None:
        try:
            return self._index_frequency
        except AttributeError:
            self._index_frequency = self.index_.freqstr
            return self._index_frequency

    @property
    def frame_size(self: PouchingSchedule) -> int:
        return self.index_.size

    @property
    def schedule_frame(self: PouchingSchedule) -> pd.DataFrame:
        try:
            return self._schedule_frame
        except AttributeError:
            self._schedule_frame = pd.DataFrame(
                index=self.index_[self.schedule_mask],
                columns=self.active_machines
            )
            return self._schedule_frame

    @property
    def schedule_mask(self: PouchingSchedule) -> pd.Series[bool]:
        try:
            return self._schedule_mask
        except AttributeError:
            self._schedule_mask = pd.Series(False, index=self.index_)
            for date_ in self.scheduled_days:
                day_start_time = self.work_week.__getattribute__(
                    f'{date_.strftime("%a").lower()}_start_time'
                )
                day_end_time = self.work_week.__getattribute__(
                    f'{date_.strftime("%a").lower()}_end_time'
                )
                day_start_dt = dt.combine(date_, day_start_time)
                day_end_dt = dt.combine(date_, day_end_time)
                self._schedule_mask[day_start_dt:day_end_dt] = True
            return self._schedule_mask

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

    @property
    def prior_week(self: PouchingSchedule) -> str:
        try:
            return self._prior_year_week
        except AttributeError:
            prior_week_start = self.start_datetime - timedelta(days=7)
            self._prior_year_week = dt.strftime(
                prior_week_start, _YEAR_WEEK_FORMAT
            )
            return self._prior_year_week

    @property
    def next_week(self: PouchingSchedule) -> str:
        try:
            return self._next_year_week
        except AttributeError:
            next_week_start = self.start_datetime + timedelta(days=7)
            self._next_year_week = dt.strftime(
                next_week_start, _YEAR_WEEK_FORMAT
            )
            return self._next_year_week

    def reload(self: PouchingSchedule) -> None:
        self.__init__(year_week=self.year_week)

    @staticmethod
    def refresh() -> None:
        _schedule_frame = _three_week_frame()
        for work_order in PouchingSchedule.scheduled_jobs():
            machine: str = work_order.machine
            cropped_frame = _schedule_frame.loc[current_hour():, machine]
            cropped_frame = map_work_order(
                work_order=work_order, _frame=cropped_frame
            )
            _schedule_frame[machine] = cropped_frame

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
                WorkOrder.machine
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
                WorkOrder.machine
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
    def on_machine(machine: str | None) -> WorkOrder | None:
        return db.session.execute(
            db.select(WorkOrder).where(
                and_(
                    WorkOrder.machine == machine,
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
        year_week = dt.strftime(dt.now(), _YEAR_WEEK_FORMAT)
        super().__init__(year_week=year_week)

    @property
    def current_week_hour(self: CurrentPouchingSchedule) -> int:
        self._current_week_hour = self.week_hour(dt.now())
        return self._current_week_hour

    @property
    def current_hour(self: CurrentPouchingSchedule) -> dt:
        return current_hour()
