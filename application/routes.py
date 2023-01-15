import json

from datetime import datetime as dt
from flask import (flash, redirect, render_template, url_for)

from application import app, db
from application.form import NewWorkOrder
from application.models import ScheduledJobs


def _make_schedule():
    pass

def current_hour():
    """
    Returns integer representing the hour of the week.
    """
    return dt.now().weekday() * 24 + dt.now().hour

def parking_lot():
    """
    Returns database query for all 'Parking Lot' jobs.
    """
    return (
        ScheduledJobs.query.filter(
            ScheduledJobs.status == 'Parking Lot'
            ).order_by(ScheduledJobs.date.desc()).all()
        )

@app.route('/')
def index():
    weekdays = [
        'Monday', 'Tuesday', 'Wednesday',
        'Thursday', 'Friday', 'Saturday', 'Sunday'
        ]
    lines = range(5, 10) # 5 - 9
    active_jobs = ScheduledJobs.query.filter(
        ScheduledJobs.status in ['on Line {x}' for x in lines]
        ).all()

    return render_template(
        'index.html', weekdays=weekdays, lines=lines,
        parking_lot=parking_lot(), current_hour=current_hour()
        )

@app.route('/view-all')
def all_work_orders():
    entries = ScheduledJobs.query.order_by(ScheduledJobs.date.desc()).all()
    return render_template('workorders.html', entries=entries)

@app.route('/add', methods=["POST", "GET"])
def add_work_order():
    new_work_order_form = NewWorkOrder()
    if new_work_order_form.validate_on_submit():
        entry = ScheduledJobs(
            product=new_work_order_form.product.data, lot_id=new_work_order_form.lot_id.data,
            lot_number=new_work_order_form.lot_number.data,
            strip_lot_number=new_work_order_form.strip_lot_number.data,
            status=new_work_order_form.status.data
            )
        db.session.add(entry)
        db.session.commit()
        flash(
            f'{new_work_order_form.product.data} {new_work_order_form.lot_id.data} '
            f'(Lot #{new_work_order_form.lot_number.data}) added successfully.',
            'success'
            )
        return redirect(url_for('index'))
    return render_template('add.html', title='Add Work Order', form=new_work_order_form)

@app.route('/delete/<int:lot_number>')
def delete(lot_number):
    entry = ScheduledJobs.query.get_or_404(int(lot_number))
    db.session.delete(entry)
    db.session.commit()
    flash(f'Lot {lot_number} deleted.', 'danger')
    return redirect(url_for('view_work_orders'))

@app.route('/performance')
def performance():
    type_comparison = (
        db.session.query(
                db.func.sum(ScheduledJobs.lot_number),
                ScheduledJobs.product
            ).group_by(
                ScheduledJobs.product
                ).order_by(
                    ScheduledJobs.product
                    ).all()
        )

    product_comparison = (
        db.session.query(
                db.func.sum(ScheduledJobs.lot_number),
                ScheduledJobs.status
            ).group_by(
                ScheduledJobs.status
                ).order_by(
                    ScheduledJobs.status
                    ).all()
        )

    dates = (
        db.session.query(
                db.func.sum(ScheduledJobs.lot_number),
                ScheduledJobs.date
            ).group_by(
                ScheduledJobs.date
                ).order_by(
                    ScheduledJobs.date
                    ).all()
        )

    income_category = []
    for lot_numbers, _ in product_comparison:
        income_category.append(lot_numbers)

    income_expense = []
    for total_lot_number, _ in type_comparison:
        income_expense.append(total_lot_number)

    chart3_data = []
    dates_label = []
    for lot_number, date in dates:
        dates_label.append(date.strftime("%m-%d-%y"))
        chart3_data.append(lot_number)

    return render_template(
        'performance.html', 
        chart1_data=json.dumps(income_expense),
        income_category=json.dumps(income_category),
        chart3_data=json.dumps(chart3_data),
        dates_label =json.dumps(dates_label)
        )