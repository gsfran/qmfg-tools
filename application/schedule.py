from datetime import date, time, timedelta
from datetime import datetime as dt
import pandas as pd

from application import db
from application.models import WorkOrders


class Schedule:

    def __init__(self, datetime_: dt, lines: list[int]) -> None:
        self.year_week = datetime_.strftime('%Y-%V')
        self.lines = lines
        
        self._set_dates(datetime_)
        self._update_work_orders()
        self._init_schedule_frame()

    def _init_schedule_frame(self) -> None:
        self._schedule_frame = pd.DataFrame(
            index=self.lines, columns=range(168)
            )
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

    def _set_dates(self, datetime_: dt) -> None:
        self.start_date = datetime_ - timedelta(days=datetime_.weekday())
        self.start_datetime = dt.combine(self.start_date, time(0))
        self.dates = [
            self.start_date + timedelta(days=_) for _ in range(7)
            ]
        self.end_date = self.dates[-1]
        self.end_datetime = dt.combine(
            self.end_date, time(23, 59, 59, 999999)
            )

    def _update_work_orders(self) -> None:
        self.work_orders = WorkOrders.query.filter(
                WorkOrders.end_datetime >= self.start_date
            ).filter(
                WorkOrders.start_datetime <= self.end_date
            ).order_by(WorkOrders.start_datetime.desc()).all()

    def get_schedule(self) -> pd.DataFrame:
        self.update_schedule()
        return self._schedule_frame

    def update_schedule(self) -> None:
        pass

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
        super().__init__(dt.now(), lines)

    def current_hour(self) -> int:
        return self.grid_hour(dt.now())