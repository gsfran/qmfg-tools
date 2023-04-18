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
from application.machines import Machine, machines
from application.models import PouchingWorkOrder, WorkWeek

_YEAR_WEEK_FORMAT: str = '%G-%V'


with open(os.environ['SCHEDULE_JSON'], 'r') as schedule_json:
    schedule_times: dict[str, str] = json.load(schedule_json)


def current_dt_snapped() -> dt:
    return snap_dt_to_grid(dt.now())


def current_year_week() -> str:
    return dt.strftime(dt.now(), _YEAR_WEEK_FORMAT)


def snap_dt_to_grid(datetime_: dt) -> dt:
    minute_ = datetime_.minute // (60 // Schedule.COLS_PER_HOUR)
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


def _map_work_order(
        work_order: PouchingWorkOrder, _frame_row: pd.Series[str],
        cols_per_hour: int
) -> pd.Series[str]:
    work_order.remaining_qty = work_order.strip_qty - work_order.pouched_qty
    work_order.remaining_time = math.ceil(
        work_order.remaining_qty / work_order.standard_rate
    )
    start_index = _get_first_open_index(_frame_row)

    if work_order.status == 'Queued':
        work_order.start_datetime = start_index

    end_index = _estimate_last_index(_frame_row, work_order, cols_per_hour)
    work_order.end_datetime = end_index

    db.session.commit()

    _frame_row[start_index:end_index] = work_order.lot_number
    return _frame_row


def _get_first_open_index(_frame_row: pd.Series[str]) -> dt:
    return snap_dt_to_grid(
        _frame_row.isna().first_valid_index().to_pydatetime()  # type: ignore
    )


def _estimate_last_index(
    _frame_row: pd.Series[str], work_order: PouchingWorkOrder,
    cols_per_hour: int
) -> dt:
    if work_order.status == 'Pouching':
        return snap_dt_to_grid(
            _frame_row.loc[current_dt_snapped():].head(
                work_order.remaining_time * cols_per_hour
            ).isna().last_valid_index().to_pydatetime()  # type: ignore
        )
    elif work_order.status == 'Queued':
        return snap_dt_to_grid(
            _frame_row.loc[snap_dt_to_grid(work_order.start_datetime):].head(
                work_order.remaining_time * cols_per_hour
            ).isna().last_valid_index().to_pydatetime()  # type: ignore
        )
    else:
        raise Exception(f'Error while scheduling {work_order}.')


def _get_machines(machine_type: str) -> list[Machine]:
    """Returns list of Machine objects of the given type.

    Returns:
        list[Machine]: Machines available for production.
    """
    machine_list: list[Machine] = []
    for mach_id in machines[machine_type].keys():
        mach = Machine.create(machine_type, mach_id)
        machine_list.append(mach)

    if machine_list is None:
        raise Exception(f"No machines found for '{machine_type}' type.")
    return machine_list


class Schedule:
    """Schedule for a single production week.

    Returns:
        Schedule: An instance of this class.
    """

    CSS_GRID_PERIOD: timedelta = timedelta(minutes=30)
    COLS_PER_HOUR: int = int(timedelta(hours=1) / CSS_GRID_PERIOD)
    COLS_PER_DAY: int = int(timedelta(days=1) / CSS_GRID_PERIOD)
    COLS_PER_WEEK: int = COLS_PER_DAY * 7

    def __init__(self: Schedule, year_week: str, machine_type: str) -> None:
        self.year_week = year_week
        self.machine_type = machine_type
        self._init_schedule()

    def _init_schedule(self) -> None:
        self.dates
        self.schedule_tense
        self.work_week = self._get_work_week_from_db()
        self.scheduled_days = self._get_scheduled_days_from_db()

    @property
    def dates(self: Schedule) -> pd.DatetimeIndex:
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
    def machines(self: Schedule) -> list[Machine]:
        try:
            return self._machines
        except AttributeError:
            self._machines = _get_machines(
                machine_type=self.machine_type
            )
            return self._machines

    @property
    def prior_week(self: Schedule) -> str:
        try:
            return self._prior_year_week_cache
        except AttributeError:
            prior_week_start = self.start_datetime - timedelta(days=7)
            self._prior_year_week_cache = dt.strftime(
                prior_week_start, _YEAR_WEEK_FORMAT
            )
            return self._prior_year_week_cache

    @property
    def next_week(self: Schedule) -> str:
        try:
            return self._next_year_week_cache
        except AttributeError:
            next_week_start = self.start_datetime + timedelta(days=7)
            self._next_year_week_cache = dt.strftime(
                next_week_start, _YEAR_WEEK_FORMAT
            )
            return self._next_year_week_cache

    @property
    def schedule_tense(self: Schedule) -> str:
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

    def _get_work_week_from_db(self: Schedule) -> WorkWeek:
        work_week: WorkWeek = db.session.execute(
            db.select(WorkWeek).where(
                WorkWeek.year_week == self.year_week
            )
        ).scalar_one_or_none()
        if work_week is None:
            work_week = create_week(year_week=self.year_week)
        return work_week

    def _get_scheduled_days_from_db(self: Schedule) -> list[date]:
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

    @property
    def index_(self: Schedule) -> pd.DatetimeIndex:
        try:
            return self._frame_index_cache
        except AttributeError:
            self._frame_index_cache = pd.date_range(
                start=self.start_datetime,
                end=self.end_datetime,
                freq=Schedule.CSS_GRID_PERIOD
            )
            return self._frame_index_cache

    @property
    def schedule_frame(self: Schedule) -> pd.DataFrame:
        try:
            return self._schedule_frame_cache
        except AttributeError:
            self._schedule_frame_cache = pd.DataFrame(
                index=self.schedule_mask.index[self.schedule_mask],
                columns=[m.short_name for m in self.machines]
            )
            return self._schedule_frame_cache

    @property
    def _next_3_weeks_frame(self: Schedule) -> pd.DataFrame:
        current_week = CurrentSchedule(machine_type=self.machine_type)
        week_2_obj = Schedule(
            year_week=current_week.next_week, machine_type=self.machine_type
        )
        _frame = pd.concat([
            CurrentSchedule(machine_type=self.machine_type).schedule_frame,
            week_2_obj.schedule_frame
        ])
        week_3_obj = Schedule(
            year_week=week_2_obj.next_week,
            machine_type=self.machine_type
        )
        _frame = pd.concat([
            _frame, week_3_obj.schedule_frame
        ])
        return _frame

    @property
    def schedule_mask(self: Schedule) -> pd.Series[bool]:
        try:
            return self._schedule_mask_cache
        except AttributeError:
            self._schedule_mask_cache: pd.Series[bool] = pd.Series(
                data=False, index=self.index_
            )
            for date_ in self.scheduled_days:
                day_start_time = self.work_week.__getattribute__(
                    f'{date_.strftime("%a").lower()}_start_time'
                )
                day_end_time = self.work_week.__getattribute__(
                    f'{date_.strftime("%a").lower()}_end_time'
                )
                start_index = dt.combine(date_, day_start_time)
                end_index = dt.combine(
                    date_, day_end_time) - Schedule.CSS_GRID_PERIOD
                self._schedule_mask_cache[start_index:end_index] = True
            return self._schedule_mask_cache

    @property
    def work_orders(self: Schedule) -> list[PouchingWorkOrder]:
        try:
            return self._work_order_cache
        except AttributeError:
            self._work_order_cache = db.session.execute(
                db.select(
                    PouchingWorkOrder
                ).where(
                    and_(
                        PouchingWorkOrder.end_datetime >= self.start_datetime,
                        PouchingWorkOrder.start_datetime < self.end_datetime
                    )
                ).order_by(
                    PouchingWorkOrder.start_datetime  # .desc()
                )
            ).scalars()
            return self._work_order_cache

    def reload(self: Schedule) -> None:
        self.__init__(
            year_week=self.year_week, machine_type=self.machine_type
        )
        self.refresh_work_orders()

    def refresh_work_orders(self: Schedule) -> None:
        """Recalculates all work orders iteratively.

        Args:
            None
        """
        self._schedule_temp_frame = self._next_3_weeks_frame
        for machine in self.machines:
            work_order_list = db.session.execute(
                db.select(
                    PouchingWorkOrder
                ).where(
                    PouchingWorkOrder.machine == machine.short_name
                ).order_by(
                    PouchingWorkOrder.queue_position
                )
            ).scalars()

            for work_order in work_order_list:
                _machine_schedule = self._schedule_temp_frame.loc[
                    current_dt_snapped():, machine.short_name
                ]
                mapped_frame = _map_work_order(
                    work_order=work_order, _frame_row=_machine_schedule,
                    cols_per_hour=Schedule.COLS_PER_HOUR
                )
                self._schedule_temp_frame[machine] = mapped_frame

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
    def dt_to_grid_column(datetime_: dt) -> int:
        """
        Returns integer representing the grid column for the
        given time.
        """
        return (
            (
                datetime_.minute // (60 // Schedule.COLS_PER_HOUR)
            ) + (
                datetime_.hour * Schedule.COLS_PER_HOUR
            ) + (
                datetime_.weekday() * Schedule.COLS_PER_DAY
            )
        )

    def __str__(self: Schedule) -> str:
        return (
            f'{self.start_datetime:%b %d, %Y} - '
            f'{self.end_datetime:%b %d, %Y}'
        )


class CurrentSchedule(Schedule):

    def __init__(self: CurrentSchedule, machine_type: str) -> None:
        super().__init__(
            year_week=current_year_week(), machine_type=machine_type
        )

    @property
    def current_grid_column(self: CurrentSchedule) -> int:
        self._current_grid_column = self.dt_to_grid_column(dt.now())
        return self._current_grid_column

    @property
    def current_column(self: CurrentSchedule) -> dt:
        return current_dt_snapped()
