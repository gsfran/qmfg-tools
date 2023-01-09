from application import db
from datetime import datetime

class ScheduledJobs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(30), default = 'income', nullable=False)
    category = db.Column(db.String(30), nullable = False, default='unknown')
    date = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    lot_number = db.Column(db.Integer, nullable = False)