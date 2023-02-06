from __future__ import annotations

import math
import pandas as pd

from datetime import time
from datetime import datetime as dt

from sqlalchemy import or_, and_

from application import db


class WorkOrders(db.Model):
    product = db.Column(db.String(30), nullable=False)
    product_name = db.Column(db.String(30), nullable=False)
    short_name = db.Column(db.String(10), nullable=False)
    item_number = db.Column(db.String(30), nullable=False)
    
    lot_id = db.Column(db.String(5), nullable=False)
    lot_number = db.Column(db.Integer, primary_key=True)
    strip_lot_number = db.Column(db.Integer, nullable=False, unique=True)

    strip_qty = db.Column(db.Integer, nullable=False)
    standard_rate = db.Column(db.Integer, nullable=False)
    standard_time = db.Column(db.Integer, nullable=False)
    
    status = db.Column(db.String(30), nullable=False, default='Parking Lot')
    add_datetime = db.Column(db.DateTime, nullable=False, default=dt.utcnow)
    load_datetime = db.Column(db.DateTime)
    
    line = db.Column(db.Integer)
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    pouched_qty = db.Column(db.Integer, nullable=False, default=0)
    
    remaining_qty = db.Column(db.Integer, nullable=False)
    remaining_time = db.Column(db.Integer, nullable=False)
    
    log = db.Column(db.Text, default=f'Created {add_datetime}')
    
    def __repr__(self: WorkOrders) -> str:
        return f'<WorkOrders object {self.lot_number}'
    
    @staticmethod
    def week_of(year_week: str) -> list[WorkOrders]:
        """Returns work orders on the schedule for the given week. 

        Args:
            year_week (str): The week in year-week format.

        Returns:
            list[WorkOrders]: The list of work orders.
        """
        pass
        # return db.session.execute(db.select(WorkOrders).where(
        #     WorkOrders.start_datetime
        # )) needs work
    
    @staticmethod
    def pouching() -> list[WorkOrders]:
        """
        Returns database query for all 'Pouching' work orders.
        """
        return db.session.execute(db.select(WorkOrders).where(
            WorkOrders.status == 'Pouching'
            ).order_by(WorkOrders.line)).scalars()
    
    @staticmethod
    def parking_lot() -> list[WorkOrders]:
        """
        Returns database query for all 'Parking Lot' work orders.
        """
        return db.session.execute(db.select(WorkOrders).where(
            WorkOrders.status == 'Parking Lot'
            ).order_by(WorkOrders.add_datetime.desc())
                                  ).scalars()
        
    @staticmethod
    def queued() -> list[WorkOrders]:
        """Returns db query for all Pouching and Queued jobs.

        Returns:
            list[WorkOrders]: Scheduled work orders.
        """
        return db.session.execute(db.select(WorkOrders).where(
                WorkOrders.status == 'Queued'
            )
                                  ).scalars()
        
    @staticmethod
    def scheduled_jobs() -> list[WorkOrders]:
        """Returns db query for all Pouching and Queued jobs.

        Returns:
            list[WorkOrders]: Scheduled work orders.
        """
        return db.session.execute(db.select(WorkOrders).where(
            or_(
                WorkOrders.status == 'Pouching',
                WorkOrders.status == 'Queued'
                )
            )
                                  ).scalars()
        
    @staticmethod
    def on_line(line: int) -> list[WorkOrders]:
        return db.session.execute(db.select(WorkOrders).where(
            and_(
                WorkOrders.line == line,
                WorkOrders.status == 'Pouching'
                )
        )
                                  ).scalar_one()
    

class WorkWeeks(db.Model):
    # id = db.Column(db.Integer)
    year_week = db.Column(db.String(7), primary_key=True)
    
    # [MON, TUE, WED, THU, FRI, SAT, SUN]
    prod_days = db.Column(db.Integer, nullable=False, default=0b1111100)
    
    # [0 - 23] [hr]
    workday_start_time = db.Column(db.Integer, nullable=False, default=6)
    workday_end_time = db.Column(db.Integer, nullable=False, default=23)
    
    # [5, 6, 7, 8, 9, 10, 11, 12]
    lines = db.Column(db.Integer, nullable=False, default=0b11111000)
    
    def __repr__(self: WorkWeeks) -> str:
        return f'<WorkWeeks object {self.year_week}'

    
class Line5DataBase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass