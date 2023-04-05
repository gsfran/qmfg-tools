from __future__ import annotations

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from application import db, login


@login.user_loader
def load_user(id: str):
    return db.session.execute(
        db.select(User).where(
            User.id == id
        )
    ).scalar_one()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


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
    add_datetime = db.Column(db.DateTime, nullable=False)
    load_datetime = db.Column(db.DateTime)

    line = db.Column(db.Integer)
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    pouched_qty = db.Column(db.Integer, nullable=False, default=0)

    remaining_qty = db.Column(db.Integer, nullable=False)
    remaining_time = db.Column(db.Integer, nullable=False)

    log = db.Column(db.Text, default=f'Created {add_datetime}')

    def __repr__(self: WorkOrders) -> str:
        return f'<WorkOrders object {self.lot_number}>'


class WorkWeeks(db.Model):
    # id = db.Column(db.Integer)
    year_week = db.Column(db.String(7), primary_key=True)

    # [MON, TUE, WED, THU, FRI, SAT, SUN]
    prod_days = db.Column(db.Integer, nullable=False, default=0b1111100)

    # [0 - 23] [hr]
    workday_start_time = db.Column(db.Integer, nullable=False, default=6)
    workday_end_time = db.Column(db.Integer, nullable=False, default=23)

    # [5, 6, 7, 8, 9, 10, 11, 12]
    lines = db.Column(db.Integer, nullable=False, default=0b01111100)

    def __repr__(self: WorkWeeks) -> str:
        return f'<WorkWeeks object {self.year_week}>s'


class Line5DataBase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass
