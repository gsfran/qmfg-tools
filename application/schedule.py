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
    lines: list = field(default_factory=list)
    workday_start: time = time(6)
    workday_end: time = time(23)

    def __post_init__(self) -> None:
        self._build_week()
        self._update_work_orders()
        self._init_schedule_frame()

    def _init_schedule_frame(self) -> None:
        self._schedule_frame = pd.DataFrame(
            columns=self.lines, index=pd.date_range(
                start=self.start_datetime, end=self.end_datetime,
                freq='h'
                )
            )
        self._schedule_frame['scheduled'] = False
        self._update_frame()

    def _update_frame(self) -> None:
        self._update_work_orders()
        for work_order in self.work_orders:
            self._map_work_order(work_order)
        pass

    def _map_work_order(self, work_order: WorkOrders) -> None:
        if work_order.start_datetime < self.start_datetime:
            work_order._start = self.grid_hour(work_order.start_datetime)
            work_order._end = self.grid_hour(work_order.end_datetime)

    def _build_week(self) -> None:
        self.start_datetime = dt.strptime(f'{self.year_week}-Mon', '%G-%V-%a')
        self.end_date = self.start_datetime + timedelta(days=6)
        self.end_datetime = dt.combine(self.end_date, time().max)
        self.dates = pd.date_range(
            self.start_datetime, self.end_datetime,
            freq='d'
            )

    def _update_work_orders(self) -> None:
        self.work_orders = WorkOrders.query.filter(
                WorkOrders.end_datetime >= self.start_datetime
            ).filter(
                WorkOrders.start_datetime <= self.end_datetime
            ).order_by(WorkOrders.start_datetime.desc()).all()

    def _refresh(self) -> None:
        self.__init__(
            self.year_week, self.lines,
            self.workday_start, self.workday_end
            )
        
    def previous_year_week(self) -> str:
        prev_week_start = self.start_datetime - timedelta(days=7)
        prev_year_week = dt.strftime(prev_week_start, '%G-%V')
        
        return prev_year_week
        

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


class CurrentSchedule(Schedule):

    def __init__(self, lines: list[int]) -> None:
        year_week = dt.strftime(dt.now(), '%G-%V')
        super().__init__(year_week=year_week, lines=lines)

    def current_hour(self) -> int:
        return self.grid_hour(dt.now())