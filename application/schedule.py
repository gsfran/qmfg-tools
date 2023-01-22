import datetime
from datetime import datetime as dt
import pandas as pd

from application import db
from application.models import WorkOrders


class Schedule:

    def __init__(self, date_: datetime.date, lines: list[int]) -> None:
        self.year_week = date_.strftime('%Y-%V')
        self.lines = lines
        self._init_schedule_frame()
        self._set_dates(date_)
        self._set_work_orders()

    def _init_schedule_frame(self) -> None:
        self._schedule_frame = pd.DataFrame(
            index=self.lines, columns=range(168)
            )

    def _set_dates(self, date_: dt) -> None:
        self.start_date = date_ - datetime.timedelta(days=date_.weekday())
        self.dates = [
            self.start_date
            + datetime.timedelta(days=_)
            for _ in range(7)
            ]
        self.end_date = self.dates[-1]

    def _set_work_orders(self) -> None:
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
    def parking_lot() -> db.Query:
        """
        Returns database query for all 'Parking Lot' jobs.
        """
        return (
            WorkOrders.query.filter(
                WorkOrders.status == 'Parking Lot'
                ).order_by(WorkOrders.add_datetime.desc()).all()
            )


class CurrentSchedule(Schedule):

    def __init__(self, lines: list[int]) -> None:
        super().__init__(dt.now().date(), lines)

    def current_hour(self) -> int:
        """
        Returns integer representing the current hour
        of the week. Ranges from 0 - 167, with 0 representing
        12AM - 1AM Monday morning.
        """
        return (dt.now().weekday() * 24) + dt.now().hour