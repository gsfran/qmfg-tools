from __future__ import annotations

from datetime import datetime as dt
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from application import db, login
from application.machines import Machine


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


class PouchWorkOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(30), nullable=False)
    product_name = db.Column(db.String(30), nullable=False)
    short_name = db.Column(db.String(10), nullable=False)
    item_number = db.Column(db.String(30), nullable=False)

    lot_id = db.Column(db.String(5), nullable=False)
    lot_number = db.Column(db.Integer, index=True, unique=True)
    strip_lot_number = db.Column(db.Integer, index=True)

    strip_qty = db.Column(db.Integer)
    standard_rate = db.Column(db.Integer)
    standard_time = db.Column(db.Integer)

    status = db.Column(db.String(30), default='Parking Lot')
    created_dt = db.Column(db.DateTime, default=dt.utcnow)
    load_dt = db.Column(db.DateTime, default=None)

    machine = db.Column(db.Integer, default=None)
    priority = db.Column(db.Integer, default=None)
    pouching_start_dt = db.Column(db.DateTime, default=None)
    pouching_end_dt = db.Column(db.DateTime, default=None)
    pouched_qty = db.Column(db.Integer, nullable=False, default=0)

    remaining_qty = db.Column(db.Integer, nullable=False)
    remaining_time = db.Column(db.Integer, nullable=False)

    log = db.Column(db.Text, default=f'{created_dt}\tCreated.')

    def move_to_parking_lot(self: PouchWorkOrder) -> None:
        self.machine = None
        self.priority = None
        self.status = 'Parking Lot'
        self.load_dt = None
        self.pouching_start_dt = None
        self.pouching_end_dt = None
        self.log += f'{dt.now()}\tMoved to Parking Lot.'

    def schedule_to_machine(
        self: PouchWorkOrder, machine: Machine, priority: int
    ) -> None:
        self.machine = machine
        self.priority = priority
        self.status = 'Queued'
        self.load_dt = dt.now()
        self.log += f'{dt.now}\tScheduled to {machine}.'

    def close_work_order(self: PouchWorkOrder) -> None:
        self.priority = None
        self.status = 'Closed'
        self.pouching_end_dt = dt.now()
        self.log += f'{dt.now()}\tClosed.'

    def __repr__(self: PouchWorkOrder) -> str:
        return f'<WorkOrders object {self.lot_number}>'


class WorkWeek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year_week = db.Column(db.String(7), index=True, nullable=False)

    mon_start_time = db.Column(db.Time, default=None)
    tue_start_time = db.Column(db.Time, default=None)
    wed_start_time = db.Column(db.Time, default=None)
    thu_start_time = db.Column(db.Time, default=None)
    fri_start_time = db.Column(db.Time, default=None)
    sat_start_time = db.Column(db.Time, default=None)
    sun_start_time = db.Column(db.Time, default=None)

    mon_end_time = db.Column(db.Time, default=None)
    tue_end_time = db.Column(db.Time, default=None)
    wed_end_time = db.Column(db.Time, default=None)
    thu_end_time = db.Column(db.Time, default=None)
    fri_end_time = db.Column(db.Time, default=None)
    sat_end_time = db.Column(db.Time, default=None)
    sun_end_time = db.Column(db.Time, default=None)

    # iTrak Lines
    itrak_5 = db.Column(db.Boolean, default=False)
    itrak_6 = db.Column(db.Boolean, default=False)
    itrak_7 = db.Column(db.Boolean, default=False)
    itrak_8 = db.Column(db.Boolean, default=False)
    itrak_9 = db.Column(db.Boolean, default=False)
    itrak_10 = db.Column(db.Boolean, default=False)
    itrak_11 = db.Column(db.Boolean, default=False)

    # dipstick pouchers
    dipstick_A = db.Column(db.Boolean, default=False)
    dipstick_B = db.Column(db.Boolean, default=False)
    dipstick_C = db.Column(db.Boolean, default=False)
    dipstick_D = db.Column(db.Boolean, default=False)
    dipstick_E = db.Column(db.Boolean, default=False)
    dipstick_F = db.Column(db.Boolean, default=False)
    dipstick_G = db.Column(db.Boolean, default=False)
    dipstick_H = db.Column(db.Boolean, default=False)

    # swab pouchers
    swab_auto = db.Column(db.Boolean, default=False)
    swab_carousel = db.Column(db.Boolean, default=False)

    # web laminators
    # web spotters
    # web dispensers
    # nitro laminators

    def __repr__(self: WorkWeek) -> str:
        return f'<WorkWeeks object {self.year_week}>s'
