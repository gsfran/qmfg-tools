import datetime
from datetime import datetime as dt

from application import db
from application.models import WorkOrders


class Schedule:
    
    def __init__(self, date_: datetime.date) -> None:
        self.year_week = date_.strftime('%Y-%V')
        self.set_dates(date_)
        self.jobs = self.get_jobs()

    def set_dates(self, date_: dt) -> None:
        self.start_date = date_ - datetime.timedelta(days=date_.weekday())
        self.dates = [self.start_date + datetime.timedelta(days=_) for _ in range(7)]
    
    def get_jobs(self):
        return None
        self.active_jobs = WorkOrders.query.filter(
                (WorkOrders.start_date <= self.dates[-1])
                or (WorkOrders.end_date >= self.dates[0])
            ).order_by(WorkOrders.date.desc()).all()
        
    def on_line(line_number: int):
        return (
            WorkOrders.query.filter(
                WorkOrders.status == f'on Line {line_number}'
            ).order_by(WorkOrders.date.desc()).all()
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
    
    def parking_lot(self):
        """
        Returns database query for all 'Parking Lot' jobs.
        """
        return (
            WorkOrders.query.filter(
                WorkOrders.status == 'Parking Lot'
                ).order_by(WorkOrders.date.desc()).all()
            )