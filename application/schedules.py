from __future__ import annotations

import json
import math
import os
from datetime import date
from datetime import datetime as dt
from datetime import time, timedelta

import pandas as pd
from sqlalchemy import and_

from application import db
from application.machines import Machine, machines
from application.models import PouchWorkOrder, WorkWeek

_YEAR_WEEK_FORMAT: str = '%G-%V'


with open(os.environ['SCHEDULE_JSON'], 'r') as SCHEDULE_JSON:
    schedule_times: dict[str, str] = json.load(SCHEDULE_JSON)


def _dt_now_to_grid() -> dt:
    return _snap_dt_to_grid(dt.now())


def current_year_week() -> str:
    return dt.strftime(dt.now(), _YEAR_WEEK_FORMAT)


def _snap_dt_to_grid(datetime_: dt) -> dt:
    minute_ = ((datetime_.minute // (60 // Schedule.COLS_PER_HOUR)) * 
               (60 // Schedule.COLS_PER_HOUR)
               )
    return datetime_.replace(minute=minute_, second=0, microsecond=0)


def _create_work_week(year_week: str) -> WorkWeek:
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
        work_order: PouchWorkOrder, _frame_row: pd.Series[str],
        COLS_PER_HOUR: int
) -> pd.Series[str]:
    work_order.remaining_qty = work_order.strip_qty - work_order.pouched_qty
    work_order.remaining_time = math.ceil(
        work_order.remaining_qty / work_order.standard_rate
    )
    start_index = _get_first_open_index(_frame_row)
    print(start_index)

    if work_order.status == 'Queued':
        work_order.pouching_start_dt = start_index

    end_index = _estimate_last_index(_frame_row, work_order, COLS_PER_HOUR)
    work_order.pouching_end_dt = end_index
    print(end_index)

    _frame_row[start_index:end_index] = work_order.lot_number
    db.session.commit()
    return _frame_row


def _get_first_open_index(_frame_row: pd.Series[str]) -> dt:
    # type: ignore
    return _frame_row.loc[
        _frame_row.isna()
    ].index[0].to_pydatetime()  # type: ignore


def _estimate_last_index(
    _frame_row: pd.Series[str], work_order: PouchWorkOrder,
    COLS_PER_HOUR: int
) -> dt:
    column_span = int(
        work_order.remaining_time * COLS_PER_HOUR
    )
    if work_order.status == 'Pouching':
        return _snap_dt_to_grid(
            _frame_row.index[column_span].to_pydatetime()  # type: ignore
        )
    elif work_order.status == 'Queued':
        return _snap_dt_to_grid(
            _frame_row.loc[
                work_order.pouching_start_dt:
            ].index[column_span].to_pydatetime()  # type: ignore
        )
    else:
        raise Exception(f'Error while scheduling {work_order}.')


def _get_machines(machine_family: str) -> list[Machine]:
    """
    Returns list of Machine objects of the given type.

    Returns:
        list[Machine]: Machines available for production.
    """
    machine_list: list[Machine] = []
    for mach_id in machines[machine_family].keys():
        mach = Machine.create(mach_id)
        machine_list.append(mach)

    if machine_list is None:
        raise Exception(f"No machines found for '{machine_family}' type.")
    return machine_list


class Schedule:
    """
    Schedule for a single production week.

    Returns:
        Schedule: An instance of this class.
    """

    CSS_GRID_PERIOD: timedelta = timedelta(minutes=30)
    COLS_PER_HOUR: int = int(timedelta(hours=1) / CSS_GRID_PERIOD)
    COLS_PER_DAY: int = int(timedelta(days=1) / CSS_GRID_PERIOD)
    COLS_PER_WEEK: int = COLS_PER_DAY * 7

    def __init__(self: Schedule, year_week: str, machine_family: str) -> None:
        self.year_week = year_week
        self.machine_family = machine_family
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
                machine_family=self.machine_family
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
            work_week = _create_work_week(year_week=self.year_week)
        return work_week

    def _get_scheduled_days_from_db(self: Schedule) -> list[date]:
        """
        Returns a list of datetime.date objects representing
        the days scheduled for the given week.

        Returns:
            list[date]: List of days scheduled for the week.
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
        # try:
        #     return self._schedule_frame_cache
        # except AttributeError:
        #     self._schedule_frame_cache = pd.DataFrame(
        #         index=self.schedule_mask.index[self.schedule_mask],
        #         columns=[m.short_name for m in self.machines]
        #     )
        #     return self._schedule_frame_cache
        self._schedule_frame_cache = pd.DataFrame(
            index=self.schedule_mask.index[self.schedule_mask],
            columns=[m.short_name for m in self.machines]
        )
        return self._schedule_frame_cache

    @property
    def _next_3_weeks_frame(self: Schedule) -> pd.DataFrame:
        current_week = CurrentSchedule(machine_family=self.machine_family)
        week_2_obj = Schedule(
            year_week=current_week.next_week, machine_family=self.machine_family
        )
        _frame = pd.concat([
            CurrentSchedule(machine_family=self.machine_family).schedule_frame,
            week_2_obj.schedule_frame
        ])
        week_3_obj = Schedule(
            year_week=week_2_obj.next_week,
            machine_family=self.machine_family
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
    def work_orders(self: Schedule) -> list[PouchWorkOrder]:
        try:
            return self._work_order_cache
        except AttributeError:
            self._work_order_cache = db.session.execute(
                db.select(
                    PouchWorkOrder
                ).where(
                    and_(
                        PouchWorkOrder.pouching_end_dt >= self.start_datetime,
                        PouchWorkOrder.pouching_start_dt < self.end_datetime
                    )
                ).order_by(
                    PouchWorkOrder.pouching_start_dt  # .desc()
                )
            ).scalars().all()
            return self._work_order_cache

    def _reinitialize(self: Schedule) -> None:
        self.__init__(
            year_week=self.year_week, machine_family=self.machine_family
        )
        self._refresh_work_orders

    def _refresh_work_orders(self: Schedule) -> None:
        """
        Recalculates all work orders iteratively.

        Args:
            None
        """
        self._schedule_temp_frame = self._next_3_weeks_frame
        for machine in self.machines:
            self._refresh_machine_work_orders(machine)

    def _refresh_machine_work_orders(self: Schedule, machine: Machine) -> None:
        work_orders = self.scheduled(machine=machine)
        work_orders = db.session.execute(
            db.select(
                PouchWorkOrder
            ).where(
                PouchWorkOrder.machine == machine.short_name
            ).order_by(
                PouchWorkOrder.priority
            )
        ).scalars().all()

        for work_order in work_orders:
            _machine_schedule = self._schedule_temp_frame.loc[
                _dt_now_to_grid():, machine.short_name
            ]
            print(work_order)
            _machine_schedule = _map_work_order(
                work_order=work_order, _frame_row=_machine_schedule,
                COLS_PER_HOUR=Schedule.COLS_PER_HOUR
            )
            # print(_machine_schedule.head(200))
            self._schedule_temp_frame[machine.short_name] = _machine_schedule

    @staticmethod
    def parking_lot() -> list[PouchWorkOrder]:
        """
        Returns database query for all 'Parking Lot' jobs.
        """
        return db.session.execute(
            db.select(PouchWorkOrder).where(
                PouchWorkOrder.status == 'Parking Lot'
            ).order_by(
                PouchWorkOrder.created_dt.desc()
            )
        ).scalars().all()

    @staticmethod
    def pouching(
        machine: Machine | None = None
    ) -> list[PouchWorkOrder] | None:
        """
        Returns database query for all 'Pouching' jobs.
        """
        if machine is None:
            return db.session.execute(
                db.select(PouchWorkOrder).where(
                    PouchWorkOrder.priority == 0
                ).order_by(
                    PouchWorkOrder.machine
                )
            ).scalars().all()
        else:
            return db.session.execute(
                db.select(PouchWorkOrder).where(
                    and_(
                        PouchWorkOrder.priority == 0,
                        PouchWorkOrder.machine == machine.short_name
                    )
                )
            ).scalars().all()

    @staticmethod
    def queued(machine: Machine | None = None) -> list[PouchWorkOrder] | None:
        """
        Returns db query for all Queued jobs.
        Optionally,

        Returns:
            list[WorkOrders]: Scheduled work orders.
        """
        if machine is None:
            return db.session.execute(
                db.select(PouchWorkOrder).where(
                    PouchWorkOrder.priority > 0
                ).order_by(
                    PouchWorkOrder.priority
                ).order_by(PouchWorkOrder.machine)
            ).scalars().all()
        else:
            return db.session.execute(
                db.select(PouchWorkOrder).where(
                    and_(
                        PouchWorkOrder.priority > 0,
                        PouchWorkOrder.machine == machine.short_name
                    )
                ).order_by(PouchWorkOrder.priority)
            ).scalars().all()

    @staticmethod
    def scheduled(
        machine: Machine | None = None
    ) -> list[PouchWorkOrder] | None:
        """Returns db query for all Pouching and Queued jobs.

        Returns:
            list[WorkOrders]: Scheduled work orders.
        """
        if machine is None:
            return db.session.execute(
                db.select(PouchWorkOrder).where(
                    PouchWorkOrder.priority >= 0
                ).order_by(PouchWorkOrder.priority)
            ).scalars().all()
        else:
            return db.session.execute(
                db.select(PouchWorkOrder).where(
                    and_(
                        PouchWorkOrder.priority >= 0,
                        PouchWorkOrder.machine == machine.short_name
                    )
                ).order_by(PouchWorkOrder.priority)
            ).scalars().all()

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

    def __init__(self: CurrentSchedule, machine_family: str) -> None:
        super().__init__(
            year_week=current_year_week(), machine_family=machine_family
        )

    @property
    def current_grid_column(self: CurrentSchedule) -> int:
        self._current_grid_column = self.dt_to_grid_column(dt.now())
        return self._current_grid_column

    @property
    def current_column(self: CurrentSchedule) -> dt:
        return _dt_now_to_grid()
