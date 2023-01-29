from __future__ import annotations

from datetime import datetime

from application import db


class WorkOrders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(30), nullable=False)
    product_name = db.Column(db.String(30), nullable=False)
    short_name = db.Column(db.String(10), nullable=False)
    item_number = db.Column(db.String(30), nullable=False)
    
    lot_id = db.Column(db.String(5), nullable=False)
    lot_number = db.Column(db.Integer, nullable=False, unique=True)
    strip_lot_number = db.Column(db.Integer, nullable=False, unique=True)

    strip_qty = db.Column(db.Integer, nullable=False)
    standard_rate = db.Column(db.Integer, nullable=False)
    standard_time = db.Column(db.Integer, nullable=False)
    
    status = db.Column(db.String(30), nullable=False, default='Parking Lot')
    add_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
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


class WorkWeeks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year_week = db.Column(db.String(7), unique=True)
    
    prod_days = db.Column(db.Integer, nullable=False, default=0b1111100)
    workday_start_time = db.Column(db.Integer, nullable=False, default=6)
    workday_end_time = db.Column(db.Integer, nullable=False, default=23)
    
    lines = db.Column(db.Integer, nullable=False, default=0b11111000)
    
    def __repr__(self: WorkWeeks) -> str:
        return f'<WorkWeeks object {self.year_week}'
    
class Line5DataBase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass