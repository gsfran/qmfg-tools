import datetime
from datetime import datetime as dt

from application import db
from application.models import WorkOrders


class Schedule:
    
    def __init__(self, date_: datetime.date) -> None:
        self.year_week = date_.strftime('%Y-%V')
        self.set_week_dates(date_)
        self.set_work_orders()

    def set_week_dates(self, date_: dt) -> None:
        self.start_date = date_ - datetime.timedelta(days=date_.weekday())
        self.dates = [
            self.start_date
            + datetime.timedelta(days=_)
            for _ in range(7)
            ]
        self.end_date = self.dates[-1]

    def set_work_orders(self) -> None:
        self.work_orders = WorkOrders.query.filter(
                WorkOrders.end_datetime >= self.start_date
            ).filter(
                WorkOrders.start_datetime <= self.end_date
            ).order_by(WorkOrders.start_datetime.desc()).all()
        
    @staticmethod
    def parking_lot():
        """
        Returns database query for all 'Parking Lot' jobs.
        """
        return (
            WorkOrders.query.filter(
                WorkOrders.status == 'Parking Lot'
                ).order_by(WorkOrders.add_datetime.desc()).all()
            )
        
class CurrentSchedule(Schedule):

    def __init__(self):
        super().__init__(dt.now().date())
        
    def current_hour(self) -> int:
        """
        Returns integer representing the current hour
        of the week. Ranges from 0 - 167, with 0 representing
        12AM - 1AM Monday morning.
        """
        return (dt.now().weekday() * 24) + dt.now().hour
