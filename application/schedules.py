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
from application.machines import Machine, machine_list, get_default_machines_from_json
from application.models import WorkOrder, WorkWeek

_YEAR_WEEK_FORMAT: str = '%G-%V'


def current_year_week() -> str:
    """Returns the year_week string for the current week.

    Returns:
        str: RegEx-like expression encoding year and week.
    """
    return dt.strftime(dt.now(), _YEAR_WEEK_FORMAT)


def get_default_schedule_from_json() -> dict[str, str]:
    """Reads default production start/end times from the
    schedule.json file specified in .env
    """
    json_file = os.environ['SCHEDULE_JSON']
    with open(json_file, 'r') as j:
        default_schedule = json.load(j)
    return default_schedule


def _dt_now_to_grid() -> dt:
    """Returns the index of the last time division
    prior to the user's current time.

    Returns:
        dt: datetime of the most recent grid column
    """
    return _snap_dt_to_grid(dt.now())


def _snap_dt_to_grid(datetime_: dt) -> dt:
    """Returns the index of the last time division
    prior to the given datetime.

    Args:
        datetime_ (dt): datetime to snap

    Returns:
        dt: datetime of the grid column prior to the given datetime
    """
    minute_ = ((datetime_.minute // (60 // Schedule.COLS_PER_HOUR)) *
               (60 // Schedule.COLS_PER_HOUR)
               )
    return datetime_.replace(minute=minute_, second=0, microsecond=0)


def _create_work_week(year_week: str) -> WorkWeek:
    """Instantiates and returns a WorkWeek Object
    for the given year_week string.

    Args:
        year_week (str): year_week string of the specified format

    Returns:
        WorkWeek: Instance of the WorkWeek object
        (specified in application/models.py).
    """
    work_week = WorkWeek(year_week=year_week)
    schedule_times = get_default_schedule_from_json()
    for day_, time_ in schedule_times.items():
        if time_ is not None:
            work_week.__setattr__(
                day_, dt.strptime(time_, '%H:%M').time()
            )

    machines = get_default_machines_from_json()
    for machine_, active_ in machines.items():
        work_week.__setattr__(machine_, active_)
    db.session.add(work_week)
    db.session.commit()
    return work_week


def _map_work_order(
        work_order: WorkOrder, _frame_row: pd.Series[str],
        COLS_PER_HOUR: int
) -> pd.Series[str]:
    """Maps the given WorkOrder object to the pandas Series
    representing the specified machine's schedule.

    Args:\n
        work_order (WorkOrder): Work order to be scheduled\n
        _frame_row (pd.Series[str]): A row of the schedule Dataframe\n
        COLS_PER_HOUR (int): Constant which sets the time divisions each hour\n

    Returns:
        pd.Series[str]: The updated machine schedule
        with the work order mapped.
    """
    work_order.remaining_qty = work_order.strip_qty - work_order.pouched_qty
    work_order.remaining_time = math.ceil(
        work_order.remaining_qty / work_order.standard_rate
    )
    start_index = _get_first_open_index(_frame_row)

    if work_order.status == 'Queued':
        work_order.pouching_start_dt = start_index

    end_index = _estimate_last_index(_frame_row, work_order, COLS_PER_HOUR)
    work_order.pouching_end_dt = end_index

    _frame_row[start_index:end_index] = work_order.lot_number
    db.session.commit()

    return _frame_row


def _get_first_open_index(_frame_row: pd.Series[str]) -> dt:
    """Returns the datetime representing the
    first open index for the given machine schedule.

    Args:
        _frame_row (pd.Series[str]): A row of the schedule Dataframe

    Returns:
        dt: datetime of the first open schedule index
    """
    _index = _frame_row.loc[
        _frame_row.isna()
    ].index[0].to_pydatetime()  # type: ignore
    print(f'{_index=}')
    return _index


def _estimate_last_index(
    _frame_row: pd.Series[str], work_order: WorkOrder,
    COLS_PER_HOUR: int
) -> dt:
    """Returns the datetime representing the grid column after
    pouching is estimated to end.

    Args:\n
        _frame_row (pd.Series[str]): A row of the schedule Dataframe\n
        work_order (WorkOrder): The work order to be scheduled\n
        COLS_PER_HOUR (int): Constant which sets the time divisions each hour\n

    Raises:
        Exception: Raises if attempting to schedule a work_order
        with status other than 'Pouching' or 'Queued'

    Returns:
        dt: datetime of the schedule index after estimated completion
    """
    column_span = int(
        work_order.remaining_time * COLS_PER_HOUR
    )
    index_num = column_span - 1
    print(f'{index_num=}')
    if work_order.status == 'Pouching':
        return _frame_row.index[index_num].to_pydatetime()  # type: ignore
    elif work_order.status == 'Queued':
        return _frame_row.loc[
            work_order.pouching_start_dt:
        ].index[index_num].to_pydatetime()  # type: ignore
    else:
        raise Exception(f'Error while scheduling {work_order}.')


class Schedule:

    # Time period representing the width of each CSS grid column
    CSS_GRID_PERIOD: timedelta = timedelta(minutes=30)

    # Number of grid columns/time divisions per hour
    COLS_PER_HOUR: int = int(timedelta(hours=1) / CSS_GRID_PERIOD)

    # Number of grid columns/time divisions per day
    COLS_PER_DAY: int = COLS_PER_HOUR * 24

    # Number of grid columns/time divisions per week
    COLS_PER_WEEK: int = COLS_PER_DAY * 7

    def __init__(self: Schedule, year_week: str, machine_family: str) -> None:
        self.year_week = year_week
        self.machine_family = machine_family
        self._init_schedule()

    def _init_schedule(self: Schedule) -> None:
        self.dates
        self.schedule_tense
        self.work_week = self._get_work_week_from_db()
        self.scheduled_days = self._get_scheduled_days_from_db()

    def _reinitialize(self: Schedule) -> None:
        """Reinitializes the schedule, used after changing
        week parameters or as a generic refresh.

        Args:
            self (Schedule)

        Returns:
            None
        """
        self.__init__(
            year_week=self.year_week, machine_family=self.machine_family
        )
        self._refresh_work_orders

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
            self._machines = machine_list(
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
        self._schedule_frame_cache = pd.DataFrame(
            index=self.schedule_mask.index[self.schedule_mask],
            columns=[m.short_name for m in self.machines]
        )
        return self._schedule_frame_cache

    @property
    def _next_3_weeks_frame(self: Schedule) -> pd.DataFrame:
        current_week = CurrentSchedule(machine_family=self.machine_family)
        week_2_obj = Schedule(
            year_week=current_week.next_week,
            machine_family=self.machine_family
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
    def work_orders(self: Schedule) -> list[WorkOrder]:
        try:
            return self._work_order_cache
        except AttributeError:
            self._work_order_cache = db.session.execute(
                db.select(
                    WorkOrder
                ).where(
                    and_(
                        WorkOrder.pouching_end_dt    # type: ignore
                        >= self.start_datetime,
                        WorkOrder.pouching_start_dt  # type: ignore
                        < self.end_datetime
                    )
                ).order_by(
                    WorkOrder.pouching_start_dt
                )
            ).scalars().all()
            return self._work_order_cache

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
                WorkOrder
            ).where(
                WorkOrder.machine == machine.short_name
            ).order_by(
                WorkOrder.priority
            )
        ).scalars().all()

        for work_order in work_orders:
            _machine_schedule = self._schedule_temp_frame.loc[
                _dt_now_to_grid():, machine.short_name
            ]
            _machine_schedule = _map_work_order(
                work_order=work_order, _frame_row=_machine_schedule,
                COLS_PER_HOUR=Schedule.COLS_PER_HOUR
            )
            print(work_order.__repr__())
            self._schedule_temp_frame[machine.short_name] = _machine_schedule

    @staticmethod
    def parking_lot() -> list[WorkOrder]:
        """
        Returns database query for all 'Parking Lot' jobs.
        """
        return db.session.execute(
            db.select(WorkOrder).where(
                WorkOrder.status == 'Parking Lot'
            ).order_by(
                WorkOrder.created_dt.desc()
            )
        ).scalars().all()

    @staticmethod
    def pouching(
        machine: Machine | None = None
    ) -> list[WorkOrder]:
        """
        Returns database query for all 'Pouching' jobs.
        """
        if machine is None:
            return db.session.execute(
                db.select(WorkOrder).where(
                    WorkOrder.priority == 0
                ).order_by(
                    WorkOrder.machine
                )
            ).scalars().all()
        else:
            return db.session.execute(
                db.select(WorkOrder).where(
                    and_(
                        WorkOrder.priority == 0,                 # type: ignore
                        WorkOrder.machine == machine.short_name  # type: ignore
                    )
                )
            ).scalars().all()

    @staticmethod
    def queued(machine: Machine | None = None) -> list[WorkOrder]:
        """
        Returns db query for queued jobs on the machine.
        If machine is None, returns all queued jobs on all machines.

        Returns:
            list[WorkOrders]: Scheduled work orders.
        """
        if machine is None:
            return db.session.execute(
                db.select(WorkOrder).where(
                    WorkOrder.priority > 0  # type: ignore
                ).order_by(
                    WorkOrder.priority
                ).order_by(WorkOrder.machine)
            ).scalars().all()
        else:
            return db.session.execute(
                db.select(WorkOrder).where(
                    and_(
                        WorkOrder.priority > 0,  # type: ignore
                        WorkOrder.machine        # type: ignore
                        == machine.short_name
                    )
                ).order_by(WorkOrder.priority)
            ).scalars().all()

    @staticmethod
    def scheduled(
        machine: Machine | None = None
    ) -> list[WorkOrder]:
        """Returns db query for all Pouching and Queued jobs.

        Returns:
            list[WorkOrders]: Scheduled work orders.
        """
        if machine is None:
            return db.session.execute(
                db.select(WorkOrder).where(
                    WorkOrder.priority >= 0  # type: ignore
                ).order_by(WorkOrder.priority)
            ).scalars().all()
        else:
            return db.session.execute(
                db.select(WorkOrder).where(
                    and_(
                        WorkOrder.priority >= 0,  # type: ignore
                        WorkOrder.machine         # type: ignore
                        == machine.short_name
                    )
                ).order_by(WorkOrder.priority)
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
