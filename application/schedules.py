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
from application.models import PouchingWorkOrder, WorkWeek


_YEAR_WEEK_FORMAT: str = '%G-%V'


with open(os.environ['SCHEDULE_JSON'], 'r') as schedule_json:
    schedule_times: dict[str, str] = json.load(schedule_json)


def current_grid_column() -> dt:
    return snap_to_grid(dt.now())


def snap_to_grid(datetime_: dt) -> dt:
    minute_ = datetime_.minute // (60 // PouchingSchedule.COLS_PER_HOUR)
    return datetime_.replace(minute=minute_, second=0, microsecond=0)


def create_week(year_week: str) -> WorkWeek:
    print(f'Creating week {year_week}')
    work_week = WorkWeek(year_week=year_week)
    for day_, time_ in schedule_times.items():
        if time_ is not None:
            work_week.__setattr__(day_, dt.strptime(time_, '%H:%M').time())
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
    work_order: PouchingWorkOrder, _frame: pd.Series[str],
    cols_per_hour: int
) -> pd.Series[str]:
    work_order.remaining_qty = work_order.strip_qty - work_order.pouched_qty
    work_order.remaining_time = math.ceil(
        work_order.remaining_qty / work_order.standard_rate
    )
    wo_start = get_first_column(_frame)

    if work_order.status == 'Queued':
        work_order.start_datetime = wo_start

    wo_end = get_last_column(_frame, work_order, cols_per_hour)
    work_order.end_datetime = wo_end

    db.session.commit()

    _frame[wo_start:wo_end] = work_order.lot_number
    return _frame


def get_first_column(_frame: pd.Series[str]) -> dt:
    return snap_to_grid(
        _frame.isna().first_valid_index().to_pydatetime()  # type: ignore
    )


def get_last_column(
    _frame: pd.Series[str], work_order: PouchingWorkOrder,
    cols_per_hour: int
) -> dt:
    if work_order.status == 'Pouching':
        return _frame.loc[current_grid_column():].head(
            work_order.remaining_time * cols_per_hour
        ).isna().last_valid_index().to_pydatetime()  # type: ignore

    elif work_order.status == 'Queued':
        return _frame.loc[work_order.start_datetime:].head(
            work_order.remaining_time * cols_per_hour
        ).isna().last_valid_index().to_pydatetime()  # type: ignore

    else:
        raise Exception(f'Error while scheduling {work_order}.')


class PouchingSchedule:
    """Schedule for pouching that covers a single production week.

    Returns:
        Instance of PouchingSchedule class.
    """

    CSS_COLUMN_SIZE: timedelta = timedelta(minutes=30)
    COLS_PER_HOUR: int = int(timedelta(hours=1) / CSS_COLUMN_SIZE)
    COLS_PER_DAY: int = int(timedelta(days=1) / CSS_COLUMN_SIZE)
    COLS_PER_WEEK: int = COLS_PER_DAY * 7

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

        for date_ in self.dates:
            scheduled = self.work_week.__getattribute__(
                f'{date_.strftime("%a").lower()}_start_time'
            )
            if scheduled is None:
                continue
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
                freq=PouchingSchedule.CSS_COLUMN_SIZE
            )
            return self._frame_index

    @property
    def schedule_frame(self: PouchingSchedule) -> pd.DataFrame:
        try:
            return self._schedule_frame
        except AttributeError:
            self._schedule_frame = pd.DataFrame(
                index=self.schedule_mask.index[self.schedule_mask],
                columns=self.active_machines
            )
            return self._schedule_frame

    @property
    def schedule_mask(self: PouchingSchedule) -> pd.Series[bool]:
        try:
            return self._schedule_mask
        except AttributeError:
            self._schedule_mask: pd.Series[bool] = pd.Series(
                data=False, index=self.index_
            )
            for date_ in self.scheduled_days:
                day_start_time = self.work_week.__getattribute__(
                    f'{date_.strftime("%a").lower()}_start_time'
                )
                day_end_time = self.work_week.__getattribute__(
                    f'{date_.strftime("%a").lower()}_end_time'
                )
                day_start_dt = dt.combine(date_, day_start_time)
                day_end_dt = dt.combine(
                    date_, day_end_time) - PouchingSchedule.CSS_COLUMN_SIZE
                self._schedule_mask[day_start_dt:day_end_dt] = True
            return self._schedule_mask

    @property
    def work_orders(self: PouchingSchedule) -> list[PouchingWorkOrder]:
        def _get_work_orders() -> list[PouchingWorkOrder]:
            return db.session.execute(
                db.select(PouchingWorkOrder).where(
                    and_(
                        PouchingWorkOrder.end_datetime >= self.start_datetime,
                        PouchingWorkOrder.start_datetime < self.end_datetime
                    )
                ).order_by(
                    PouchingWorkOrder.start_datetime  # .desc()
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
            cropped_frame = _schedule_frame.loc[current_grid_column():, machine]
            mapped_frame = map_work_order(
                work_order=work_order, _frame=cropped_frame,
                cols_per_hour=PouchingSchedule.COLS_PER_HOUR
            )
            _schedule_frame[machine] = mapped_frame

    @staticmethod
    def parking_lot() -> list[PouchingWorkOrder]:
        """
        Returns database query for all 'Parking Lot' jobs.
        """
        return db.session.execute(
            db.select(PouchingWorkOrder).where(
                PouchingWorkOrder.status == 'Parking Lot'
            ).order_by(
                PouchingWorkOrder.add_datetime.desc()
            )
        ).scalars()

    @staticmethod
    def pouching() -> list[PouchingWorkOrder]:
        """
        Returns database query for all 'Pouching' jobs.
        """
        return db.session.execute(
            db.select(PouchingWorkOrder).where(
                PouchingWorkOrder.status == 'Pouching'
            ).order_by(
                PouchingWorkOrder.machine
            )
        ).scalars()

    @staticmethod
    def queued() -> list[PouchingWorkOrder]:
        """Returns db query for all Queued jobs.

        Returns:
            list[WorkOrders]: Scheduled work orders.
        """
        return db.session.execute(
            db.select(PouchingWorkOrder).where(
                PouchingWorkOrder.status == 'Queued'
            ).order_by(
                PouchingWorkOrder.machine
            )
        ).scalars()

    @staticmethod
    def scheduled_jobs() -> list[PouchingWorkOrder]:
        """Returns db query for all Pouching and Queued jobs.

        Returns:
            list[WorkOrders]: Scheduled work orders.
        """
        return db.session.execute(
            db.select(PouchingWorkOrder).where(
                or_(
                    PouchingWorkOrder.status == 'Pouching',
                    PouchingWorkOrder.status == 'Queued'
                )
            )
        ).scalars()

    @staticmethod
    def on_machine(machine: str | None) -> PouchingWorkOrder | None:
        return db.session.execute(
            db.select(PouchingWorkOrder).where(
                and_(
                    PouchingWorkOrder.machine == machine,
                    PouchingWorkOrder.status == 'Pouching'
                )
            )
        ).scalar_one_or_none()

    @staticmethod
    def grid_column(datetime_: dt) -> int:
        """
        Returns integer representing the grid column for the
        given time.
        """
        return datetime_.hour + (
            datetime_.weekday() * PouchingSchedule.COLS_PER_DAY
        )

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
    def current_grid_column(self: CurrentPouchingSchedule) -> int:
        self._current_grid_column = self.grid_column(dt.now())
        return self._current_grid_column

    @property
    def current_column(self: CurrentPouchingSchedule) -> dt:
        return current_grid_column()
