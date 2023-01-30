from __future__ import annotations

import math
import pandas as pd

from datetime import time
from datetime import datetime as dt

from sqlalchemy import or_

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
            ).order_by(WorkOrders.add_datetime.desc())).scalars()
        
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
    def update_work_order(work_order: WorkOrders, _frame: pd.Series) -> WorkOrders:
        work_order.remaining_qty = work_order.strip_qty - work_order.pouched_qty
        work_order.remaining_time = (
            math.ceil(
                work_order.remaining_qty / work_order.standard_rate
                )
            )
        _frame_start = _frame[_frame.isna().sort_index()].index[0]
        _frame_end = _frame[_frame_start:].head(work_order.remaining_time).index[-1]
        
        work_order.start_datetime = dt.combine(_frame_start.date(), time(_frame_start.hour))
        work_order.end_datetime = dt.combine(_frame_end.date(), time(_frame_end.hour))
        
        _frame[_frame_start:_frame_end] = work_order.lot_number
        
        return work_order, _frame
    

class WorkWeeks(db.Model):
    # id = db.Column(db.Integer)
    year_week = db.Column(db.String(7), primary_key=True)
    
    prod_days = db.Column(db.Integer, nullable=False, default=0b1111100)
    workday_start_time = db.Column(db.Integer, nullable=False, default=6)
    workday_end_time = db.Column(db.Integer, nullable=False, default=23)
    
    lines = db.Column(db.Integer, nullable=False, default=0b11111000)
    
    def __repr__(self: WorkWeeks) -> str:
        return f'<WorkWeeks object {self.year_week}'
    
class Line5DataBase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass